from datetime import date

import pytest

from model.approval_model import ApprovalModel
from model.order import OrderValidationError
from model.order_model import OrderModel
from model.order_repository import OrderRepository
from model.production_job import ProductionValidationError
from model.production_model import ProductionModel
from model.production_repository import ProductionRepository
from model.sample_model import SampleModel
from model.sample_repository import SampleRepository


@pytest.fixture
def sample_model(tmp_path):
    model = SampleModel(repository=SampleRepository(str(tmp_path / "samples.json")))
    model.register("S-1", "Wafer-A", 10.0, 0.9, 100)
    model.register("S-ZERO", "Wafer-Zero", 10.0, 0.0, 5)
    return model


@pytest.fixture
def order_model(tmp_path, sample_model):
    repository = OrderRepository(str(tmp_path / "orders.json"))
    return OrderModel(
        repository=repository,
        sample_model=sample_model,
        date_provider=lambda: date(2026, 7, 15),
    )


@pytest.fixture
def production_model(tmp_path, sample_model, order_model):
    repository = ProductionRepository(str(tmp_path / "production_jobs.json"))
    return ProductionModel(repository=repository, sample_model=sample_model, order_model=order_model)


@pytest.fixture
def approval_model(order_model, sample_model, production_model):
    return ApprovalModel(order_model=order_model, sample_model=sample_model, production_model=production_model)


def test_approve_rejects_unknown_order_id(approval_model):
    with pytest.raises(OrderValidationError):
        approval_model.approve("UNKNOWN")


def test_reject_rejects_unknown_order_id(approval_model):
    with pytest.raises(OrderValidationError):
        approval_model.reject("UNKNOWN")


@pytest.mark.parametrize("already_processed_status", ["CONFIRMED", "PRODUCING", "REJECTED"])
def test_approve_rejects_order_not_in_reserved_status(approval_model, order_model, already_processed_status):
    order = order_model.reserve("S-1", "Customer-A", 5)
    order_model.update_status(order.order_id, already_processed_status)

    with pytest.raises(OrderValidationError):
        approval_model.approve(order.order_id)


@pytest.mark.parametrize("already_processed_status", ["CONFIRMED", "PRODUCING", "REJECTED"])
def test_reject_rejects_order_not_in_reserved_status(approval_model, order_model, already_processed_status):
    order = order_model.reserve("S-1", "Customer-A", 5)
    order_model.update_status(order.order_id, already_processed_status)

    with pytest.raises(OrderValidationError):
        approval_model.reject(order.order_id)


def test_approve_confirms_order_and_decreases_stock_when_stock_is_sufficient(
    approval_model, order_model, sample_model
):
    order = order_model.reserve("S-1", "Customer-A", 20)

    updated_order, shortage_quantity = approval_model.approve(order.order_id)

    assert updated_order.status == "CONFIRMED"
    assert shortage_quantity is None
    assert sample_model.find_by_id("S-1").stock_quantity == 80


def test_approve_confirms_order_when_stock_exactly_matches_quantity(approval_model, order_model, sample_model):
    order = order_model.reserve("S-1", "Customer-A", 100)

    updated_order, shortage_quantity = approval_model.approve(order.order_id)

    assert updated_order.status == "CONFIRMED"
    assert shortage_quantity is None
    assert sample_model.find_by_id("S-1").stock_quantity == 0


def test_approve_registers_production_when_stock_is_one_short(
    approval_model, order_model, sample_model, production_model
):
    order = order_model.reserve("S-1", "Customer-A", 101)

    updated_order, shortage_quantity = approval_model.approve(order.order_id)

    assert updated_order.status == "PRODUCING"
    assert shortage_quantity == 1
    assert sample_model.find_by_id("S-1").stock_quantity == 0
    assert production_model.current_job().order_id == order.order_id
    assert production_model.current_job().shortage_quantity == 1


def test_approve_registers_full_quantity_as_shortage_when_stock_is_zero(
    approval_model, order_model, sample_model, production_model, tmp_path
):
    sample_model.register("S-EMPTY", "Wafer-Empty", 10.0, 0.9, 0)
    order = order_model.reserve("S-EMPTY", "Customer-A", 15)

    updated_order, shortage_quantity = approval_model.approve(order.order_id)

    assert updated_order.status == "PRODUCING"
    assert shortage_quantity == 15
    assert sample_model.find_by_id("S-EMPTY").stock_quantity == 0
    assert production_model.current_job().shortage_quantity == 15


def test_approve_rolls_back_completely_when_production_registration_fails_due_to_zero_yield(
    approval_model, order_model, sample_model, production_model
):
    order = order_model.reserve("S-ZERO", "Customer-A", 20)

    with pytest.raises(ProductionValidationError):
        approval_model.approve(order.order_id)

    assert order_model.find_by_id(order.order_id).status == "RESERVED"
    assert sample_model.find_by_id("S-ZERO").stock_quantity == 5
    assert production_model.current_job() is None


def test_reject_transitions_reserved_order_to_rejected_without_affecting_stock(
    approval_model, order_model, sample_model
):
    order = order_model.reserve("S-1", "Customer-A", 10)

    updated_order = approval_model.reject(order.order_id)

    assert updated_order.status == "REJECTED"
    assert sample_model.find_by_id("S-1").stock_quantity == 100


def test_general_stock_unaffected_after_production_completes_for_shortage_order(
    approval_model, order_model, sample_model, production_model
):
    order = order_model.reserve("S-1", "Customer-A", 101)
    approval_model.approve(order.order_id)
    job = production_model.current_job()

    production_model.record_progress(job.actual_production_quantity)

    assert order_model.find_by_id(order.order_id).status == "CONFIRMED"
    assert sample_model.find_by_id("S-1").stock_quantity == 0


def test_list_reserved_when_no_orders_returns_empty(approval_model):
    assert approval_model.list_reserved() == []


def test_list_reserved_includes_only_reserved_status_orders(approval_model, order_model):
    reserved_order = order_model.reserve("S-1", "Customer-A", 5)
    confirmed_order = order_model.reserve("S-1", "Customer-B", 3)
    approval_model.approve(confirmed_order.order_id)
    rejected_order = order_model.reserve("S-1", "Customer-C", 2)
    approval_model.reject(rejected_order.order_id)

    reserved_order_ids = [order.order_id for order in approval_model.list_reserved()]

    assert reserved_order_ids == [reserved_order.order_id]


def test_approval_state_persists_after_restart_with_new_instances(tmp_path):
    sample_repository = SampleRepository(str(tmp_path / "samples.json"))
    order_repository = OrderRepository(str(tmp_path / "orders.json"))
    production_repository = ProductionRepository(str(tmp_path / "production_jobs.json"))

    first_sample_model = SampleModel(repository=sample_repository)
    first_sample_model.register("S-1", "Wafer-A", 10.0, 0.9, 100)
    first_order_model = OrderModel(
        repository=order_repository,
        sample_model=first_sample_model,
        date_provider=lambda: date(2026, 7, 15),
    )
    first_production_model = ProductionModel(
        repository=production_repository, sample_model=first_sample_model, order_model=first_order_model
    )
    first_approval_model = ApprovalModel(
        order_model=first_order_model, sample_model=first_sample_model, production_model=first_production_model
    )
    order = first_order_model.reserve("S-1", "Customer-A", 20)
    first_approval_model.approve(order.order_id)

    restarted_sample_model = SampleModel(repository=sample_repository)
    restarted_order_model = OrderModel(
        repository=order_repository,
        sample_model=restarted_sample_model,
        date_provider=lambda: date(2026, 7, 15),
    )

    assert restarted_order_model.find_by_id(order.order_id).status == "CONFIRMED"
    assert restarted_sample_model.find_by_id("S-1").stock_quantity == 80
