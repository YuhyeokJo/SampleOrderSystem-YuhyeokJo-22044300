from datetime import date

import pytest

from model.order import OrderValidationError
from model.order_model import OrderModel
from model.order_repository import OrderRepository
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


def test_reserve_success_returns_order_with_reserved_status(order_model):
    order = order_model.reserve("S-1", "Customer-A", 5)

    assert order.order_id == "ORD-20260715-0001"
    assert order.sample_id == "S-1"
    assert order.customer_name == "Customer-A"
    assert order.quantity == 5
    assert order.status == "RESERVED"


def test_reserve_rejects_unregistered_sample_id(order_model):
    with pytest.raises(OrderValidationError):
        order_model.reserve("UNKNOWN", "Customer-A", 5)


def test_reserve_rejects_empty_customer_name(order_model):
    with pytest.raises(OrderValidationError):
        order_model.reserve("S-1", "", 5)


@pytest.mark.parametrize("invalid_quantity", [0, -1])
def test_reserve_rejects_non_positive_quantity(order_model, invalid_quantity):
    with pytest.raises(OrderValidationError):
        order_model.reserve("S-1", "Customer-A", invalid_quantity)


def test_reserve_rejects_non_integer_quantity(order_model):
    with pytest.raises(OrderValidationError):
        order_model.reserve("S-1", "Customer-A", 1.5)


def test_reserve_allows_quantity_of_exactly_one(order_model):
    order = order_model.reserve("S-1", "Customer-A", 1)

    assert order.quantity == 1


def test_reserve_generates_sequential_order_numbers_for_same_date(order_model):
    first_order = order_model.reserve("S-1", "Customer-A", 1)
    second_order = order_model.reserve("S-1", "Customer-B", 2)
    third_order = order_model.reserve("S-1", "Customer-C", 3)

    assert first_order.order_id == "ORD-20260715-0001"
    assert second_order.order_id == "ORD-20260715-0002"
    assert third_order.order_id == "ORD-20260715-0003"


def test_reserve_resets_sequence_when_date_changes(tmp_path, sample_model):
    repository = OrderRepository(str(tmp_path / "orders.json"))
    current_date = [date(2026, 7, 15)]
    model = OrderModel(
        repository=repository,
        sample_model=sample_model,
        date_provider=lambda: current_date[0],
    )

    first_day_order = model.reserve("S-1", "Customer-A", 1)
    current_date[0] = date(2026, 7, 16)
    second_day_order = model.reserve("S-1", "Customer-B", 1)

    assert first_day_order.order_id == "ORD-20260715-0001"
    assert second_day_order.order_id == "ORD-20260716-0001"


def test_all_when_no_orders_reserved_returns_empty(order_model):
    assert order_model.all() == []


def test_find_by_id_returns_none_when_order_not_found(order_model):
    assert order_model.find_by_id("UNKNOWN") is None


def test_update_status_changes_status_and_persists(order_model):
    order = order_model.reserve("S-1", "Customer-A", 5)

    updated_order = order_model.update_status(order.order_id, "PRODUCING")

    assert updated_order.status == "PRODUCING"
    assert order_model.find_by_id(order.order_id).status == "PRODUCING"


def test_update_status_rejects_unknown_order_id(order_model):
    with pytest.raises(OrderValidationError):
        order_model.update_status("UNKNOWN", "CONFIRMED")
