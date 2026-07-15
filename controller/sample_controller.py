from model.sample import SampleValidationError
from model.sample_model import SampleModel
from view.sample_view import SampleView


class SampleController:
    """시료 관리 메뉴의 흐름을 제어한다."""

    def __init__(self, model=None, view=None):
        self.model = model or SampleModel()
        self.view = view or SampleView()

    def run(self):
        actions = {
            "1": self._register_sample,
            "2": self._list_samples,
            "3": self._search_samples,
        }
        while True:
            self.view.show_menu()
            choice = self.view.prompt_choice()
            if choice == "4":
                self.view.show_message("종료합니다.")
                break
            action = actions.get(choice)
            if action is None:
                self.view.show_message("올바르지 않은 선택입니다.")
                continue
            action()

    def _register_sample(self):
        sample_id = self.view.prompt_sample_id()
        name = self.view.prompt_name()
        raw_avg_production_time = self.view.prompt_avg_production_time()
        raw_yield_rate = self.view.prompt_yield_rate()
        raw_stock_quantity = self.view.prompt_stock_quantity()

        try:
            avg_production_time = float(raw_avg_production_time)
            yield_rate = float(raw_yield_rate)
            stock_quantity = int(raw_stock_quantity)
        except ValueError:
            self.view.show_message("등록 실패: 숫자 형식이 올바르지 않습니다.")
            return

        try:
            sample = self.model.register(
                sample_id, name, avg_production_time, yield_rate, stock_quantity
            )
        except SampleValidationError as error:
            self.view.show_message(f"등록 실패: {error}")
            return
        self.view.show_message(f"등록 완료: {sample.sample_id} ({sample.name})")

    def _list_samples(self):
        self.view.show_samples(self.model.all())

    def _search_samples(self):
        keyword = self.view.prompt_search_keyword()
        results = self.model.search_by_name(keyword)
        if not results:
            self.view.show_message("일치하는 시료가 없습니다.")
            return
        self.view.show_samples(results)
