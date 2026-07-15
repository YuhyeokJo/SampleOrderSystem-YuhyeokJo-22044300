from datetime import date

from controller.order_controller import OrderController
from model.order_model import OrderModel
from model.order_repository import OrderRepository
from model.sample_model import SampleModel
from model.sample_repository import SampleRepository


class FakeView:
    def __init__(self, choices, sample_id="S-1", customer_name="Customer-A", quantity="5"):
        self._choices = iter(choices)
        self._sample_id = sample_id
        self._customer_name = customer_name
        self._quantity = quantity
        self.messages = []
        self.input_summaries = []
        self.reservation_successes = []

    def show_menu(self):
        pass

    def prompt_choice(self):
        return next(self._choices)

    def prompt_sample_id(self):
        return self._sample_id

    def prompt_customer_name(self):
        return self._customer_name

    def prompt_quantity(self):
        return self._quantity

    def show_message(self, message):
        self.messages.append(message)

    def show_input_summary(self, sample_id, customer_name, quantity):
        self.input_summaries.append((sample_id, customer_name, quantity))

    def show_reservation_success(self, order):
        self.reservation_successes.append(order)


def make_controller(choices, tmp_path, **view_kwargs):
    sample_model = SampleModel(repository=SampleRepository(str(tmp_path / "samples.json")))
    sample_model.register("S-1", "Wafer-A", 10.0, 0.9, 100)
    model = OrderModel(
        repository=OrderRepository(str(tmp_path / "orders.json")),
        sample_model=sample_model,
        date_provider=lambda: date(2026, 7, 15),
    )
    view = FakeView(choices, **view_kwargs)
    return OrderController(model=model, view=view), view


def test_reserve_flow_saves_order_and_reports_success(tmp_path):
    controller, view = make_controller(["1", "2"], tmp_path)

    controller.run()

    assert len(controller.model.all()) == 1
    assert view.input_summaries == [("S-1", "Customer-A", 5)]
    assert len(view.reservation_successes) == 1
    assert view.reservation_successes[0].order_id == "ORD-20260715-0001"


def test_reserve_flow_rejects_unregistered_sample_id(tmp_path):
    controller, view = make_controller(["1", "2"], tmp_path, sample_id="UNKNOWN")

    controller.run()

    assert controller.model.all() == []
    assert any("접수 실패" in message for message in view.messages)


def test_reserve_flow_rejects_empty_customer_name(tmp_path):
    controller, view = make_controller(["1", "2"], tmp_path, customer_name="")

    controller.run()

    assert controller.model.all() == []
    assert any("접수 실패" in message for message in view.messages)


def test_reserve_flow_rejects_non_integer_quantity(tmp_path):
    controller, view = make_controller(["1", "2"], tmp_path, quantity="abc")

    controller.run()

    assert controller.model.all() == []
    assert any("접수 실패" in message for message in view.messages)


def test_reserve_flow_rejects_zero_quantity(tmp_path):
    controller, view = make_controller(["1", "2"], tmp_path, quantity="0")

    controller.run()

    assert controller.model.all() == []
    assert any("접수 실패" in message for message in view.messages)
