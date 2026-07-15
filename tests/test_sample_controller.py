from controller.sample_controller import SampleController
from model.sample_model import SampleModel
from model.sample_repository import SampleRepository


class FakeView:
    def __init__(self, choices):
        self._choices = iter(choices)
        self.messages = []
        self.shown_samples = []

    def show_menu(self):
        pass

    def prompt_choice(self):
        return next(self._choices)

    def prompt_sample_id(self):
        return "S-1"

    def prompt_name(self):
        return "Wafer-A"

    def prompt_avg_production_time(self):
        return "10.0"

    def prompt_yield_rate(self):
        return "0.9"

    def prompt_stock_quantity(self):
        return "100"

    def prompt_search_keyword(self):
        return "Wafer"

    def show_message(self, message):
        self.messages.append(message)

    def show_samples(self, samples):
        self.shown_samples.append(samples)


def make_controller(choices, tmp_path):
    model = SampleModel(repository=SampleRepository(str(tmp_path / "samples.json")))
    view = FakeView(choices)
    return SampleController(model=model, view=view), view


def test_register_flow_saves_sample_and_reports_success(tmp_path):
    controller, view = make_controller(["1", "4"], tmp_path)

    controller.run()

    assert controller.model.find_by_id("S-1") is not None
    assert any("등록 완료" in message for message in view.messages)


def test_register_flow_reports_failure_on_invalid_input(tmp_path):
    controller, view = make_controller(["1", "1", "4"], tmp_path)

    controller.run()

    assert any("등록 실패" in message for message in view.messages)


def test_list_flow_with_no_samples_shows_empty_result(tmp_path):
    controller, view = make_controller(["2", "4"], tmp_path)

    controller.run()

    assert view.shown_samples == [[]]


def test_search_flow_with_no_match_reports_not_found(tmp_path):
    controller, view = make_controller(["3", "4"], tmp_path)

    controller.run()

    assert any("일치하는 시료가 없습니다" in message for message in view.messages)
