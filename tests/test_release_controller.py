from datetime import date

from controller.release_controller import ReleaseController
from model.order_model import OrderModel
from model.order_repository import OrderRepository
from model.release_model import ReleaseModel
from model.sample_model import SampleModel
from model.sample_repository import SampleRepository


class FakeView:
    def __init__(self, choices, order_id="ORD-1"):
        self._choices = iter(choices)
        self._order_id = order_id
        self.messages = []
        self.confirmed_orders_shown = None
        self.release_results = []

    def show_menu(self):
        pass

    def prompt_choice(self):
        return next(self._choices)

    def prompt_order_id(self):
        return self._order_id

    def show_message(self, message):
        self.messages.append(message)

    def show_confirmed_orders(self, orders):
        self.confirmed_orders_shown = orders

    def show_release_result(self, order):
        self.release_results.append(order)


def make_controller(choices, tmp_path, order_id="ORD-1"):
    sample_model = SampleModel(repository=SampleRepository(str(tmp_path / "samples.json")))
    sample_model.register("S-1", "Wafer-A", 10.0, 0.9, 100)
    order_model = OrderModel(
        repository=OrderRepository(str(tmp_path / "orders.json")),
        sample_model=sample_model,
        date_provider=lambda: date(2026, 7, 15),
    )
    model = ReleaseModel(order_model=order_model)
    view = FakeView(choices, order_id=order_id)
    return ReleaseController(model=model, view=view), view, order_model, sample_model


def test_release_flow_transitions_confirmed_order_to_release(tmp_path):
    controller, view, order_model, _ = make_controller(["2", "3"], tmp_path)
    order = order_model.reserve("S-1", "Customer-A", 5)
    order_model.update_status(order.order_id, "CONFIRMED")
    view._order_id = order.order_id

    controller.run()

    assert order_model.find_by_id(order.order_id).status == "RELEASE"
    assert len(view.release_results) == 1
    assert view.release_results[0].order_id == order.order_id


def test_release_flow_reports_failure_for_unknown_order_id(tmp_path):
    controller, view, _, _ = make_controller(["2", "3"], tmp_path, order_id="UNKNOWN")

    controller.run()

    assert any("출고 실패" in message for message in view.messages)


def test_release_flow_reports_failure_when_order_not_confirmed(tmp_path):
    controller, view, order_model, _ = make_controller(["2", "3"], tmp_path)
    order = order_model.reserve("S-1", "Customer-A", 5)
    view._order_id = order.order_id

    controller.run()

    assert any("출고 실패" in message for message in view.messages)
    assert order_model.find_by_id(order.order_id).status == "RESERVED"


def test_show_confirmed_orders_flow_when_no_orders_reports_empty(tmp_path):
    controller, view, _, _ = make_controller(["1", "3"], tmp_path)

    controller.run()

    assert view.confirmed_orders_shown == []


def test_show_confirmed_orders_flow_includes_only_confirmed_orders(tmp_path):
    controller, view, order_model, _ = make_controller(["1", "3"], tmp_path)
    reserved_order = order_model.reserve("S-1", "Customer-A", 5)
    confirmed_order = order_model.reserve("S-1", "Customer-B", 3)
    order_model.update_status(confirmed_order.order_id, "CONFIRMED")

    controller.run()

    shown_order_ids = [order.order_id for order in view.confirmed_orders_shown]
    assert shown_order_ids == [confirmed_order.order_id]
    assert reserved_order.order_id not in shown_order_ids
