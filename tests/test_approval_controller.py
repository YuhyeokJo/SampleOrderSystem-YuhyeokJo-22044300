from datetime import date

from controller.approval_controller import ApprovalController
from model.approval_model import ApprovalModel
from model.order_model import OrderModel
from model.order_repository import OrderRepository
from model.production_model import ProductionModel
from model.production_repository import ProductionRepository
from model.sample_model import SampleModel
from model.sample_repository import SampleRepository


class FakeView:
    def __init__(self, choices, order_id="ORD-1"):
        self._choices = iter(choices)
        self._order_id = order_id
        self.messages = []
        self.reserved_orders_shown = None
        self.approval_results = []
        self.rejection_results = []

    def show_menu(self):
        pass

    def prompt_choice(self):
        return next(self._choices)

    def prompt_order_id(self):
        return self._order_id

    def show_message(self, message):
        self.messages.append(message)

    def show_reserved_orders(self, orders):
        self.reserved_orders_shown = orders

    def show_approval_result(self, order, shortage_quantity):
        self.approval_results.append((order, shortage_quantity))

    def show_rejection_result(self, order):
        self.rejection_results.append(order)


def make_controller(choices, tmp_path, order_id="ORD-1"):
    sample_model = SampleModel(repository=SampleRepository(str(tmp_path / "samples.json")))
    sample_model.register("S-1", "Wafer-A", 10.0, 0.9, 100)
    sample_model.register("S-ZERO", "Wafer-Zero", 10.0, 0.0, 5)
    order_model = OrderModel(
        repository=OrderRepository(str(tmp_path / "orders.json")),
        sample_model=sample_model,
        date_provider=lambda: date(2026, 7, 15),
    )
    production_model = ProductionModel(
        repository=ProductionRepository(str(tmp_path / "production_jobs.json")),
        sample_model=sample_model,
        order_model=order_model,
    )
    model = ApprovalModel(order_model=order_model, sample_model=sample_model, production_model=production_model)
    view = FakeView(choices, order_id=order_id)
    return ApprovalController(model=model, view=view), view, order_model, sample_model


def test_approve_flow_confirms_order_when_stock_sufficient(tmp_path):
    controller, view, order_model, sample_model = make_controller(["2", "4"], tmp_path)
    order = order_model.reserve("S-1", "Customer-A", 20)
    view._order_id = order.order_id

    controller.run()

    assert order_model.find_by_id(order.order_id).status == "CONFIRMED"
    assert len(view.approval_results) == 1
    approved_order, shortage_quantity = view.approval_results[0]
    assert approved_order.order_id == order.order_id
    assert shortage_quantity is None


def test_approve_flow_reports_producing_status_when_stock_short(tmp_path):
    controller, view, order_model, sample_model = make_controller(["2", "4"], tmp_path)
    order = order_model.reserve("S-1", "Customer-A", 101)
    view._order_id = order.order_id

    controller.run()

    assert order_model.find_by_id(order.order_id).status == "PRODUCING"
    assert len(view.approval_results) == 1
    approved_order, shortage_quantity = view.approval_results[0]
    assert approved_order.order_id == order.order_id
    assert shortage_quantity == 1


def test_approve_flow_reports_failure_for_unknown_order_id(tmp_path):
    controller, view, _, _ = make_controller(["2", "4"], tmp_path, order_id="UNKNOWN")

    controller.run()

    assert any("승인 실패" in message for message in view.messages)


def test_approve_flow_reports_failure_when_production_registration_fails(tmp_path):
    controller, view, order_model, sample_model = make_controller(["2", "4"], tmp_path)
    order = order_model.reserve("S-ZERO", "Customer-A", 20)
    view._order_id = order.order_id

    controller.run()

    assert any("승인 실패" in message for message in view.messages)
    assert order_model.find_by_id(order.order_id).status == "RESERVED"
    assert sample_model.find_by_id("S-ZERO").stock_quantity == 5


def test_reject_flow_transitions_order_to_rejected(tmp_path):
    controller, view, order_model, _ = make_controller(["3", "4"], tmp_path)
    order = order_model.reserve("S-1", "Customer-A", 5)
    view._order_id = order.order_id

    controller.run()

    assert order_model.find_by_id(order.order_id).status == "REJECTED"
    assert len(view.rejection_results) == 1
    assert view.rejection_results[0].order_id == order.order_id


def test_reject_flow_reports_failure_for_unknown_order_id(tmp_path):
    controller, view, _, _ = make_controller(["3", "4"], tmp_path, order_id="UNKNOWN")

    controller.run()

    assert any("거절 실패" in message for message in view.messages)


def test_show_reserved_orders_flow_when_no_orders_reports_empty(tmp_path):
    controller, view, _, _ = make_controller(["1", "4"], tmp_path)

    controller.run()

    assert view.reserved_orders_shown == []


def test_show_reserved_orders_flow_includes_only_reserved_orders(tmp_path):
    controller, view, order_model, _ = make_controller(["1", "4"], tmp_path)
    reserved_order = order_model.reserve("S-1", "Customer-A", 5)
    confirmed_order = order_model.reserve("S-1", "Customer-B", 3)
    order_model.update_status(confirmed_order.order_id, "CONFIRMED")

    controller.run()

    shown_order_ids = [order.order_id for order in view.reserved_orders_shown]
    assert shown_order_ids == [reserved_order.order_id]
