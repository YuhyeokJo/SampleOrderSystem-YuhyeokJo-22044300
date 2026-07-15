from controller.main_controller import MainController
from model.sample_model import SampleModel


class FakeView:
    def __init__(self, choices):
        self._choices = iter(choices)
        self.summaries = []
        self.messages = []
        self.menu_shown_count = 0

    def show_summary(self, sample_count, total_stock_quantity):
        self.summaries.append((sample_count, total_stock_quantity))

    def show_menu(self):
        self.menu_shown_count += 1

    def prompt_choice(self):
        return next(self._choices)

    def show_message(self, message):
        self.messages.append(message)


class FakeSubController:
    def __init__(self):
        self.run_calls = 0

    def run(self):
        self.run_calls += 1


def test_summary_shows_no_samples_message_when_empty(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    view = FakeView(["7"])
    controller = MainController(view=view, controllers={})

    controller.run()

    assert view.summaries == [(0, 0)]


def test_summary_reports_sample_count_and_total_stock(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    sample_model = SampleModel()
    sample_model.register("S-1", "Wafer-A", 10.0, 0.9, 100)
    sample_model.register("S-2", "Wafer-B", 5.0, 0.8, 28)
    view = FakeView(["7"])
    controller = MainController(view=view, controllers={})

    controller.run()

    assert view.summaries == [(2, 128)]


def test_each_menu_choice_invokes_matching_controller(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    fake_controllers = {str(number): FakeSubController() for number in range(1, 7)}
    view = FakeView(["1", "2", "3", "4", "5", "6", "7"])
    controller = MainController(view=view, controllers=fake_controllers)

    controller.run()

    for fake_controller in fake_controllers.values():
        assert fake_controller.run_calls == 1


def test_exit_choice_ends_main_menu_loop(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    view = FakeView(["7"])
    controller = MainController(view=view, controllers={})

    controller.run()

    assert any("종료" in message for message in view.messages)
    assert view.menu_shown_count == 1


def test_invalid_choice_shows_error_and_reshows_menu(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    view = FakeView(["0", "8", "abc", "7"])
    controller = MainController(view=view, controllers={})

    controller.run()

    assert sum("올바르지 않은 선택" in message for message in view.messages) == 3
    assert view.menu_shown_count == 4


def test_returns_to_main_menu_after_sub_controller_finishes(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    fake_controller = FakeSubController()
    view = FakeView(["1", "7"])
    controller = MainController(view=view, controllers={"1": fake_controller})

    controller.run()

    assert fake_controller.run_calls == 1
    assert view.menu_shown_count == 2


def test_summary_refreshes_after_sample_registered_via_real_sample_controller(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    from controller.sample_controller import SampleController
    from view.sample_view import SampleView

    sample_model = SampleModel()

    class RegisterOnceView(SampleView):
        def __init__(self):
            self._calls = iter(["1", "4"])

        def prompt_choice(self):
            return next(self._calls)

        def prompt_sample_id(self):
            return "S-NEW"

        def prompt_name(self):
            return "New-Wafer"

        def prompt_avg_production_time(self):
            return "12.0"

        def prompt_yield_rate(self):
            return "0.95"

        def prompt_stock_quantity(self):
            return "50"

        def show_message(self, message):
            pass

    sample_controller = SampleController(model=sample_model, view=RegisterOnceView())
    view = FakeView(["1", "7"])
    controller = MainController(view=view, controllers={"1": sample_controller})

    controller.run()

    assert view.summaries == [(0, 0), (1, 50)]
