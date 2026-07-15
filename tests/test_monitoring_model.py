from datetime import date

import pytest

from model.monitoring_model import MonitoringModel
from model.order_model import OrderModel
from model.order_repository import OrderRepository
from model.sample_model import SampleModel
from model.sample_repository import SampleRepository


@pytest.fixture
def sample_model(tmp_path):
    return SampleModel(repository=SampleRepository(str(tmp_path / "samples.json")))


@pytest.fixture
def order_model(tmp_path, sample_model):
    return OrderModel(
        repository=OrderRepository(str(tmp_path / "orders.json")),
        sample_model=sample_model,
        date_provider=lambda: date(2026, 7, 15),
    )


@pytest.fixture
def monitoring_model(sample_model, order_model):
    return MonitoringModel(sample_model, order_model)


def test_default_constructor_does_not_raise(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    model = MonitoringModel()

    assert model.count_orders_by_status() == {"RESERVED": 0, "CONFIRMED": 0, "PRODUCING": 0, "RELEASE": 0}
    assert model.sample_stock_status() == []


def test_count_orders_by_status_when_no_orders_returns_all_zero(monitoring_model):
    counts = monitoring_model.count_orders_by_status()

    assert counts == {"RESERVED": 0, "CONFIRMED": 0, "PRODUCING": 0, "RELEASE": 0}


def test_count_orders_by_status_excludes_rejected_orders(monitoring_model, order_model, sample_model):
    sample_model.register("S-1", "Wafer-A", 10.0, 0.9, 100)
    order = order_model.reserve("S-1", "Customer-A", 5)
    order_model.update_status(order.order_id, "REJECTED")

    counts = monitoring_model.count_orders_by_status()

    assert counts == {"RESERVED": 0, "CONFIRMED": 0, "PRODUCING": 0, "RELEASE": 0}


def test_count_orders_by_status_counts_each_status_correctly(monitoring_model, order_model, sample_model):
    sample_model.register("S-1", "Wafer-A", 10.0, 0.9, 100)
    reserved_order = order_model.reserve("S-1", "Customer-A", 5)
    confirmed_order = order_model.reserve("S-1", "Customer-B", 3)
    producing_order = order_model.reserve("S-1", "Customer-C", 2)
    release_order = order_model.reserve("S-1", "Customer-D", 1)
    another_reserved_order = order_model.reserve("S-1", "Customer-E", 4)
    rejected_order = order_model.reserve("S-1", "Customer-F", 6)
    order_model.update_status(confirmed_order.order_id, "CONFIRMED")
    order_model.update_status(producing_order.order_id, "PRODUCING")
    order_model.update_status(release_order.order_id, "RELEASE")
    order_model.update_status(rejected_order.order_id, "REJECTED")

    counts = monitoring_model.count_orders_by_status()

    assert counts == {"RESERVED": 2, "CONFIRMED": 1, "PRODUCING": 1, "RELEASE": 1}
    assert reserved_order.status == "RESERVED"
    assert another_reserved_order.status == "RESERVED"


def test_sample_stock_status_when_no_samples_returns_empty_list(monitoring_model):
    assert monitoring_model.sample_stock_status() == []


def test_sample_stock_status_zero_stock_is_depleted_regardless_of_reserved_orders(
    monitoring_model, sample_model, order_model
):
    sample_model.register("S-1", "Wafer-A", 10.0, 0.9, 0)
    order_model.reserve("S-1", "Customer-A", 5)

    result = monitoring_model.sample_stock_status()

    assert result == [
        {"sample_id": "S-1", "name": "Wafer-A", "stock_quantity": 0, "status": "고갈"}
    ]


def test_sample_stock_status_stock_equal_to_demand_is_sufficient(monitoring_model, sample_model, order_model):
    sample_model.register("S-1", "Wafer-A", 10.0, 0.9, 10)
    order_model.reserve("S-1", "Customer-A", 4)
    order_model.reserve("S-1", "Customer-B", 6)

    result = monitoring_model.sample_stock_status()

    assert result[0]["status"] == "여유"
    assert result[0]["stock_quantity"] == 10


def test_sample_stock_status_stock_one_less_than_demand_is_shortage(monitoring_model, sample_model, order_model):
    sample_model.register("S-1", "Wafer-A", 10.0, 0.9, 9)
    order_model.reserve("S-1", "Customer-A", 4)
    order_model.reserve("S-1", "Customer-B", 6)

    result = monitoring_model.sample_stock_status()

    assert result[0]["status"] == "부족"


def test_sample_stock_status_positive_stock_with_no_reserved_orders_is_sufficient(
    monitoring_model, sample_model
):
    sample_model.register("S-1", "Wafer-A", 10.0, 0.9, 5)

    result = monitoring_model.sample_stock_status()

    assert result[0]["status"] == "여유"


def test_sample_stock_status_sums_multiple_reserved_orders_for_same_sample(
    monitoring_model, sample_model, order_model
):
    sample_model.register("S-1", "Wafer-A", 10.0, 0.9, 10)
    order_model.reserve("S-1", "Customer-A", 3)
    order_model.reserve("S-1", "Customer-B", 3)
    order_model.reserve("S-1", "Customer-C", 3)

    result = monitoring_model.sample_stock_status()

    assert result[0]["status"] == "여유"

    order_model.reserve("S-1", "Customer-D", 2)
    result_after_extra_order = monitoring_model.sample_stock_status()

    assert result_after_extra_order[0]["status"] == "부족"


def test_sample_stock_status_ignores_non_reserved_order_quantities_for_demand(
    monitoring_model, sample_model, order_model
):
    sample_model.register("S-1", "Wafer-A", 10.0, 0.9, 5)
    confirmed_order = order_model.reserve("S-1", "Customer-A", 100)
    producing_order = order_model.reserve("S-1", "Customer-B", 100)
    rejected_order = order_model.reserve("S-1", "Customer-C", 100)
    release_order = order_model.reserve("S-1", "Customer-D", 100)
    order_model.update_status(confirmed_order.order_id, "CONFIRMED")
    order_model.update_status(producing_order.order_id, "PRODUCING")
    order_model.update_status(rejected_order.order_id, "REJECTED")
    order_model.update_status(release_order.order_id, "RELEASE")

    result = monitoring_model.sample_stock_status()

    assert result[0]["status"] == "여유"
