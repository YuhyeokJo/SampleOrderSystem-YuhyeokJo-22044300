import json
from datetime import date

from model.order_model import OrderModel
from model.order_repository import OrderRepository
from model.sample_model import SampleModel
from model.sample_repository import SampleRepository


def make_sample_model(tmp_path):
    model = SampleModel(repository=SampleRepository(str(tmp_path / "samples.json")))
    model.register("S-1", "Wafer-A", 10.0, 0.9, 100)
    return model


def test_load_all_when_file_missing_returns_empty_list(tmp_path):
    repository = OrderRepository(str(tmp_path / "orders.json"))

    assert repository.load_all() == []


def test_save_all_writes_records_and_removes_tmp_file(tmp_path):
    file_path = tmp_path / "orders.json"
    repository = OrderRepository(str(file_path))
    records = [{"order_id": "ORD-20260715-0001", "sample_id": "S-1"}]

    repository.save_all(records)

    assert file_path.exists()
    assert not (tmp_path / "orders.json.tmp").exists()
    assert json.loads(file_path.read_text(encoding="utf-8")) == records


def test_order_data_persists_after_reopening_with_new_instance(tmp_path):
    sample_model = make_sample_model(tmp_path)
    order_file_path = str(tmp_path / "orders.json")
    date_provider = lambda: date(2026, 7, 15)

    first_process_model = OrderModel(
        repository=OrderRepository(order_file_path),
        sample_model=sample_model,
        date_provider=date_provider,
    )
    first_process_model.reserve("S-1", "Customer-A", 5)

    restarted_process_model = OrderModel(
        repository=OrderRepository(order_file_path),
        sample_model=sample_model,
        date_provider=date_provider,
    )
    restarted_orders = restarted_process_model.all()

    assert len(restarted_orders) == 1
    restarted_order = restarted_orders[0]
    assert restarted_order.order_id == "ORD-20260715-0001"
    assert restarted_order.sample_id == "S-1"
    assert restarted_order.customer_name == "Customer-A"
    assert restarted_order.quantity == 5
    assert restarted_order.status == "RESERVED"


def test_order_data_persists_across_multiple_reservations_and_restarts(tmp_path):
    sample_model = make_sample_model(tmp_path)
    order_file_path = str(tmp_path / "orders.json")
    date_provider = lambda: date(2026, 7, 15)

    model_before_restart = OrderModel(
        repository=OrderRepository(order_file_path),
        sample_model=sample_model,
        date_provider=date_provider,
    )
    model_before_restart.reserve("S-1", "Customer-A", 1)
    model_before_restart.reserve("S-1", "Customer-B", 2)

    model_after_restart = OrderModel(
        repository=OrderRepository(order_file_path),
        sample_model=sample_model,
        date_provider=date_provider,
    )

    assert {order.order_id for order in model_after_restart.all()} == {
        "ORD-20260715-0001",
        "ORD-20260715-0002",
    }
