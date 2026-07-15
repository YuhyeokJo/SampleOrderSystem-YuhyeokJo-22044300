from datetime import date

from controller.monitoring_controller import MonitoringController
from model.monitoring_model import MonitoringModel
from model.order_model import OrderModel
from model.order_repository import OrderRepository
from model.sample_model import SampleModel
from model.sample_repository import SampleRepository


class FakeView:
    def __init__(self, choices):
        self._choices = iter(choices)
        self.messages = []
        self.order_counts_shown = None
        self.sample_stock_status_shown = None

    def show_menu(self):
        pass

    def prompt_choice(self):
        return next(self._choices)

    def show_message(self, message):
        self.messages.append(message)

    def show_order_counts_by_status(self, counts):
        self.order_counts_shown = counts

    def show_sample_stock_status(self, stock_status_list):
        self.sample_stock_status_shown = stock_status_list


def make_controller(choices, tmp_path):
    sample_model = SampleModel(repository=SampleRepository(str(tmp_path / "samples.json")))
    order_model = OrderModel(
        repository=OrderRepository(str(tmp_path / "orders.json")),
        sample_model=sample_model,
        date_provider=lambda: date(2026, 7, 15),
    )
    model = MonitoringModel(sample_model, order_model)
    view = FakeView(choices)
    return MonitoringController(model=model, view=view), view, order_model, sample_model


def test_default_constructor_run_reports_empty_state_without_raising(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    choices = iter(["1", "2", "3"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(choices))

    controller = MonitoringController()
    controller.run()

    output = capsys.readouterr().out
    assert "[RESERVED]: 0건" in output
    assert "등록된 시료가 없습니다." in output


def test_show_order_counts_flow_when_no_orders_reports_all_zero(tmp_path):
    controller, view, _, _ = make_controller(["1", "3"], tmp_path)

    controller.run()

    assert view.order_counts_shown == {"RESERVED": 0, "CONFIRMED": 0, "PRODUCING": 0, "RELEASE": 0}


def test_show_order_counts_flow_reflects_status_mix(tmp_path):
    controller, view, order_model, sample_model = make_controller(["1", "3"], tmp_path)
    sample_model.register("S-1", "Wafer-A", 10.0, 0.9, 100)
    reserved_order = order_model.reserve("S-1", "Customer-A", 5)
    confirmed_order = order_model.reserve("S-1", "Customer-B", 3)
    rejected_order = order_model.reserve("S-1", "Customer-C", 2)
    order_model.update_status(confirmed_order.order_id, "CONFIRMED")
    order_model.update_status(rejected_order.order_id, "REJECTED")

    controller.run()

    assert view.order_counts_shown == {"RESERVED": 1, "CONFIRMED": 1, "PRODUCING": 0, "RELEASE": 0}
    assert reserved_order.status == "RESERVED"


def test_show_sample_stock_status_flow_when_no_samples_reports_empty(tmp_path):
    controller, view, _, _ = make_controller(["2", "3"], tmp_path)

    controller.run()

    assert view.sample_stock_status_shown == []


def test_show_sample_stock_status_flow_reports_depleted_and_sufficient_samples(tmp_path):
    controller, view, order_model, sample_model = make_controller(["2", "3"], tmp_path)
    sample_model.register("S-1", "Wafer-A", 10.0, 0.9, 0)
    sample_model.register("S-2", "Wafer-B", 8.0, 0.8, 10)
    order_model.reserve("S-2", "Customer-A", 4)

    controller.run()

    statuses_by_sample_id = {item["sample_id"]: item["status"] for item in view.sample_stock_status_shown}
    assert statuses_by_sample_id == {"S-1": "고갈", "S-2": "여유"}


def test_invalid_menu_choice_reports_error_message(tmp_path):
    controller, view, _, _ = make_controller(["9", "3"], tmp_path)

    controller.run()

    assert any("올바르지 않은 선택" in message for message in view.messages)
