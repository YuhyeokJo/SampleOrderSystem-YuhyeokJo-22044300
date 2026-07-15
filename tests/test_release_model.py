from datetime import date

import pytest

from model.order import OrderValidationError
from model.order_model import OrderModel
from model.order_repository import OrderRepository
from model.release_model import ReleaseModel
from model.sample_model import SampleModel
from model.sample_repository import SampleRepository


@pytest.fixture
def sample_model(tmp_path):
    model = SampleModel(repository=SampleRepository(str(tmp_path / "samples.json")))
    model.register("S-1", "Wafer-A", 10.0, 0.9, 100)
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
def release_model(order_model):
    return ReleaseModel(order_model=order_model)


def test_release_rejects_unknown_order_id(release_model):
    with pytest.raises(OrderValidationError):
        release_model.release("UNKNOWN")


@pytest.mark.parametrize("non_confirmed_status", ["RESERVED", "PRODUCING", "REJECTED", "RELEASE"])
def test_release_rejects_order_not_in_confirmed_status(release_model, order_model, non_confirmed_status):
    order = order_model.reserve("S-1", "Customer-A", 5)
    order_model.update_status(order.order_id, non_confirmed_status)

    with pytest.raises(OrderValidationError):
        release_model.release(order.order_id)


def test_release_transitions_confirmed_order_to_release_status(release_model, order_model):
    order = order_model.reserve("S-1", "Customer-A", 5)
    order_model.update_status(order.order_id, "CONFIRMED")

    updated_order = release_model.release(order.order_id)

    assert updated_order.status == "RELEASE"
    assert order_model.find_by_id(order.order_id).status == "RELEASE"


def test_release_does_not_affect_sample_stock(release_model, order_model, sample_model):
    order = order_model.reserve("S-1", "Customer-A", 5)
    order_model.update_status(order.order_id, "CONFIRMED")

    release_model.release(order.order_id)

    assert sample_model.find_by_id("S-1").stock_quantity == 100


def test_list_confirmed_when_no_orders_returns_empty(release_model):
    assert release_model.list_confirmed() == []


def test_list_confirmed_includes_only_confirmed_status_orders(release_model, order_model):
    reserved_order = order_model.reserve("S-1", "Customer-A", 5)
    confirmed_order = order_model.reserve("S-1", "Customer-B", 3)
    producing_order = order_model.reserve("S-1", "Customer-C", 2)
    rejected_order = order_model.reserve("S-1", "Customer-D", 1)
    order_model.update_status(confirmed_order.order_id, "CONFIRMED")
    order_model.update_status(producing_order.order_id, "PRODUCING")
    order_model.update_status(rejected_order.order_id, "REJECTED")

    confirmed_order_ids = [order.order_id for order in release_model.list_confirmed()]

    assert confirmed_order_ids == [confirmed_order.order_id]
    assert reserved_order.order_id not in confirmed_order_ids


def test_release_state_persists_after_restart_with_new_instances(tmp_path):
    sample_repository = SampleRepository(str(tmp_path / "samples.json"))
    order_repository = OrderRepository(str(tmp_path / "orders.json"))

    first_sample_model = SampleModel(repository=sample_repository)
    first_sample_model.register("S-1", "Wafer-A", 10.0, 0.9, 100)
    first_order_model = OrderModel(
        repository=order_repository,
        sample_model=first_sample_model,
        date_provider=lambda: date(2026, 7, 15),
    )
    first_release_model = ReleaseModel(order_model=first_order_model)
    order = first_order_model.reserve("S-1", "Customer-A", 5)
    first_order_model.update_status(order.order_id, "CONFIRMED")
    first_release_model.release(order.order_id)

    restarted_sample_model = SampleModel(repository=sample_repository)
    restarted_order_model = OrderModel(
        repository=order_repository,
        sample_model=restarted_sample_model,
        date_provider=lambda: date(2026, 7, 15),
    )

    assert restarted_order_model.find_by_id(order.order_id).status == "RELEASE"
