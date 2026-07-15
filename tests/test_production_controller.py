from datetime import date

from controller.production_controller import ProductionController
from model.order_model import OrderModel
from model.order_repository import OrderRepository
from model.production_model import ProductionModel
from model.production_repository import ProductionRepository
from model.sample_model import SampleModel
from model.sample_repository import SampleRepository


class FakeView:
    def __init__(self, choices, order_id="ORD-1", sample_id="S-1", shortage_quantity="10", produced_quantity="4"):
        self._choices = iter(choices)
        self._order_id = order_id
        self._sample_id = sample_id
        self._shortage_quantity = shortage_quantity
        self._produced_quantity = produced_quantity
        self.messages = []
        self.current_job_shown = None
        self.waiting_jobs_shown = None

    def show_menu(self):
        pass

    def prompt_choice(self):
        return next(self._choices)

    def prompt_order_id(self):
        return self._order_id

    def prompt_sample_id(self):
        return self._sample_id

    def prompt_shortage_quantity(self):
        return self._shortage_quantity

    def prompt_produced_quantity(self):
        return self._produced_quantity

    def show_message(self, message):
        self.messages.append(message)

    def show_current_job(self, job):
        self.current_job_shown = job

    def show_waiting_jobs(self, jobs):
        self.waiting_jobs_shown = jobs


def make_controller(choices, tmp_path, **view_kwargs):
    sample_model = SampleModel(repository=SampleRepository(str(tmp_path / "samples.json")))
    sample_model.register("S-1", "Wafer-A", 10.0, 0.9, 100)
    order_model = OrderModel(
        repository=OrderRepository(str(tmp_path / "orders.json")),
        sample_model=sample_model,
        date_provider=lambda: date(2026, 7, 15),
    )
    model = ProductionModel(
        repository=ProductionRepository(str(tmp_path / "production_jobs.json")),
        sample_model=sample_model,
        order_model=order_model,
    )
    view = FakeView(choices, **view_kwargs)
    return ProductionController(model=model, view=view), view, order_model


def test_register_flow_saves_job_and_reports_success(tmp_path):
    controller, view, _ = make_controller(["1", "5"], tmp_path)

    controller.run()

    assert controller.model.current_job() is not None
    assert any("등록 완료" in message for message in view.messages)


def test_register_flow_rejects_unregistered_sample_id(tmp_path):
    controller, view, _ = make_controller(["1", "5"], tmp_path, sample_id="UNKNOWN")

    controller.run()

    assert controller.model.current_job() is None
    assert any("등록 실패" in message for message in view.messages)


def test_register_flow_rejects_non_integer_shortage_quantity(tmp_path):
    controller, view, _ = make_controller(["1", "5"], tmp_path, shortage_quantity="abc")

    controller.run()

    assert controller.model.current_job() is None
    assert any("등록 실패" in message for message in view.messages)


def test_record_progress_flow_reports_accumulated_quantity_when_not_complete(tmp_path):
    controller, view, _ = make_controller(["1", "2", "5"], tmp_path, produced_quantity="4")

    controller.run()

    assert any("진행 기록 완료" in message and "4/13" in message for message in view.messages)


def test_record_progress_flow_reports_completion_and_confirms_order(tmp_path):
    sample_model = SampleModel(repository=SampleRepository(str(tmp_path / "samples.json")))
    sample_model.register("S-1", "Wafer-A", 10.0, 0.9, 100)
    order_model = OrderModel(
        repository=OrderRepository(str(tmp_path / "orders.json")),
        sample_model=sample_model,
        date_provider=lambda: date(2026, 7, 15),
    )
    order = order_model.reserve("S-1", "Customer-B", 1)
    order_model.update_status(order.order_id, "PRODUCING")
    production_model = ProductionModel(
        repository=ProductionRepository(str(tmp_path / "production_jobs.json")),
        sample_model=sample_model,
        order_model=order_model,
    )
    view = FakeView(["1", "2", "5"], order_id=order.order_id, produced_quantity="13")
    controller = ProductionController(model=production_model, view=view)

    controller.run()

    assert any("생산 완료" in message for message in view.messages)
    assert order_model.find_by_id(order.order_id).status == "CONFIRMED"


def test_record_progress_flow_rejects_when_no_job_in_progress(tmp_path):
    controller, view, _ = make_controller(["2", "5"], tmp_path)

    controller.run()

    assert any("기록 실패" in message for message in view.messages)


def test_show_current_job_flow_when_queue_empty(tmp_path):
    controller, view, _ = make_controller(["3", "5"], tmp_path)

    controller.run()

    assert view.current_job_shown is None


def test_show_waiting_jobs_flow_when_queue_empty(tmp_path):
    controller, view, _ = make_controller(["4", "5"], tmp_path)

    controller.run()

    assert view.waiting_jobs_shown == []


def test_show_waiting_jobs_flow_excludes_current_job(tmp_path):
    controller, view, order_model = make_controller(["1", "4", "5"], tmp_path, order_id="ORD-1")
    controller.model.register("ORD-2", "S-1", 20)

    controller.run()

    waiting_order_ids = [job.order_id for job in view.waiting_jobs_shown]
    assert waiting_order_ids == ["ORD-1"]
