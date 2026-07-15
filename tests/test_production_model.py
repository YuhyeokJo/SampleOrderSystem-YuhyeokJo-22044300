from datetime import date

import pytest

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
    model.register("S-ZERO", "Wafer-Zero", 10.0, 0.0, 100)
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


def make_producing_order(order_model, sample_id="S-1", customer_name="Customer-A", quantity=5):
    order = order_model.reserve(sample_id, customer_name, quantity)
    order_model.update_status(order.order_id, "PRODUCING")
    return order


def test_register_rejects_unregistered_sample_id(production_model):
    with pytest.raises(ProductionValidationError):
        production_model.register("ORD-1", "UNKNOWN", 10)


@pytest.mark.parametrize("invalid_shortage_quantity", [0, -1, 1.5])
def test_register_rejects_invalid_shortage_quantity(production_model, invalid_shortage_quantity):
    with pytest.raises(ProductionValidationError):
        production_model.register("ORD-1", "S-1", invalid_shortage_quantity)


def test_register_rejects_sample_with_zero_yield_rate(production_model):
    with pytest.raises(ProductionValidationError):
        production_model.register("ORD-1", "S-ZERO", 10)


def test_register_calculates_actual_quantity_and_total_time_with_rounding_up(production_model):
    job = production_model.register("ORD-1", "S-1", 10)

    assert job.actual_production_quantity == 13
    assert job.total_production_time == pytest.approx(130.0)


def test_register_adds_job_to_back_of_queue_and_starts_produced_quantity_at_zero(production_model):
    job = production_model.register("ORD-1", "S-1", 10)

    assert production_model.current_job() is job
    assert job.produced_quantity == 0


def test_record_progress_rejects_when_no_job_in_progress(production_model):
    with pytest.raises(ProductionValidationError):
        production_model.record_progress(5)


def test_record_progress_accumulates_across_multiple_calls(production_model):
    production_model.register("ORD-1", "S-1", 10)

    job, completed = production_model.record_progress(4)
    assert job.produced_quantity == 4
    assert completed is False

    job, completed = production_model.record_progress(3)
    assert job.produced_quantity == 7
    assert completed is False


def test_record_progress_completes_job_and_confirms_order_when_reaching_actual_quantity(
    production_model, order_model
):
    order = make_producing_order(order_model)
    job = production_model.register(order.order_id, "S-1", 10)

    job, completed = production_model.record_progress(job.actual_production_quantity)

    assert completed is True
    assert order_model.find_by_id(order.order_id).status == "CONFIRMED"
    assert production_model.current_job() is None


def test_record_progress_caps_produced_quantity_at_actual_quantity_when_overshooting(
    production_model, order_model
):
    order = make_producing_order(order_model)
    job = production_model.register(order.order_id, "S-1", 10)

    job, completed = production_model.record_progress(job.actual_production_quantity + 100)

    assert completed is True
    assert order_model.find_by_id(order.order_id).status == "CONFIRMED"


def test_record_progress_completion_rejected_when_order_not_producing(production_model, order_model):
    order = order_model.reserve("S-1", "Customer-A", 5)
    job = production_model.register(order.order_id, "S-1", 10)

    with pytest.raises(ProductionValidationError):
        production_model.record_progress(job.actual_production_quantity)

    assert order_model.find_by_id(order.order_id).status == "RESERVED"
    assert production_model.current_job() is not None
    assert production_model.current_job().order_id == order.order_id


def test_completed_job_promotes_next_waiting_job_to_current(production_model, order_model):
    first_order = make_producing_order(order_model, customer_name="Customer-A")
    second_order = order_model.reserve("S-1", "Customer-B", 5)

    first_job = production_model.register(first_order.order_id, "S-1", 10)
    second_job = production_model.register(second_order.order_id, "S-1", 20)

    production_model.record_progress(first_job.actual_production_quantity)

    current_job = production_model.current_job()
    assert current_job.order_id == second_job.order_id
    assert current_job.produced_quantity == 0


def test_current_job_returns_none_when_queue_empty(production_model):
    assert production_model.current_job() is None


def test_waiting_jobs_returns_empty_when_queue_empty(production_model):
    assert production_model.waiting_jobs() == []


def test_waiting_jobs_preserves_fifo_registration_order(production_model):
    production_model.register("ORD-1", "S-1", 10)
    production_model.register("ORD-2", "S-1", 20)
    production_model.register("ORD-3", "S-1", 30)

    waiting_order_ids = [job.order_id for job in production_model.waiting_jobs()]

    assert waiting_order_ids == ["ORD-2", "ORD-3"]


def test_production_queue_persists_after_reopening_with_new_instance(tmp_path, sample_model, order_model):
    repository_path = str(tmp_path / "production_jobs.json")

    first_process_model = ProductionModel(
        repository=ProductionRepository(repository_path),
        sample_model=sample_model,
        order_model=order_model,
    )
    first_process_model.register("ORD-1", "S-1", 10)
    first_process_model.record_progress(4)

    restarted_process_model = ProductionModel(
        repository=ProductionRepository(repository_path),
        sample_model=sample_model,
        order_model=order_model,
    )
    restarted_job = restarted_process_model.current_job()

    assert restarted_job.order_id == "ORD-1"
    assert restarted_job.produced_quantity == 4
    assert restarted_job.actual_production_quantity == 13
