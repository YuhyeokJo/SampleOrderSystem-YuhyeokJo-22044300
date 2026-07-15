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


def test_list_reserved_when_no_orders_returns_empty(order_model):
    assert order_model.list_reserved() == []


def test_list_reserved_includes_only_reserved_status_orders(order_model):
    reserved_order = order_model.reserve("S-1", "Customer-A", 5)
    confirmed_order = order_model.reserve("S-1", "Customer-B", 3)
    producing_order = order_model.reserve("S-1", "Customer-C", 2)
    rejected_order = order_model.reserve("S-1", "Customer-D", 1)
    order_model.update_status(confirmed_order.order_id, "CONFIRMED")
    order_model.update_status(producing_order.order_id, "PRODUCING")
    order_model.update_status(rejected_order.order_id, "REJECTED")

    reserved_order_ids = [order.order_id for order in order_model.list_reserved()]

    assert reserved_order_ids == [reserved_order.order_id]


def test_list_confirmed_when_no_orders_returns_empty(order_model):
    assert order_model.list_confirmed() == []


def test_list_confirmed_includes_only_confirmed_status_orders(order_model):
    reserved_order = order_model.reserve("S-1", "Customer-A", 5)
    confirmed_order = order_model.reserve("S-1", "Customer-B", 3)
    producing_order = order_model.reserve("S-1", "Customer-C", 2)
    rejected_order = order_model.reserve("S-1", "Customer-D", 1)
    released_order = order_model.reserve("S-1", "Customer-E", 4)
    order_model.update_status(confirmed_order.order_id, "CONFIRMED")
    order_model.update_status(producing_order.order_id, "PRODUCING")
    order_model.update_status(rejected_order.order_id, "REJECTED")
    order_model.update_status(released_order.order_id, "RELEASE")

    confirmed_order_ids = [order.order_id for order in order_model.list_confirmed()]

    assert confirmed_order_ids == [confirmed_order.order_id]
    assert reserved_order.order_id not in confirmed_order_ids
