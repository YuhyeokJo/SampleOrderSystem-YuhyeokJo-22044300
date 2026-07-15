from model.monitoring_model import MonitoringModel
from view.monitoring_view import MonitoringView


class MonitoringController:
    """모니터링 메뉴의 흐름을 제어한다."""

    def __init__(self, model=None, view=None, sample_model=None, order_model=None):
        self.model = model or MonitoringModel(sample_model, order_model)
        self.view = view or MonitoringView()

    def run(self):
        actions = {
            "1": self._show_order_counts,
            "2": self._show_sample_stock_status,
        }
        while True:
            self.view.show_menu()
            choice = self.view.prompt_choice()
            if choice == "3":
                self.view.show_message("종료합니다.")
                break
            action = actions.get(choice)
            if action is None:
                self.view.show_message("올바르지 않은 선택입니다.")
                continue
            action()

    def _show_order_counts(self):
        counts = self.model.count_orders_by_status()
        self.view.show_order_counts_by_status(counts)

    def _show_sample_stock_status(self):
        stock_status_list = self.model.sample_stock_status()
        self.view.show_sample_stock_status(stock_status_list)
