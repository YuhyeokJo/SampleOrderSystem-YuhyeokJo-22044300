from model.order import OrderValidationError
from model.release_model import ReleaseModel
from view.release_view import ReleaseView


class ReleaseController:
    """출고 처리 메뉴의 흐름을 제어한다."""

    def __init__(self, model=None, view=None):
        self.model = model or ReleaseModel()
        self.view = view or ReleaseView()

    def run(self):
        actions = {
            "1": self._show_confirmed_orders,
            "2": self._release_order,
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

    def _show_confirmed_orders(self):
        orders = self.model.list_confirmed()
        self.view.show_confirmed_orders(orders)

    def _release_order(self):
        order_id = self.view.prompt_order_id()

        try:
            order = self.model.release(order_id)
        except OrderValidationError as error:
            self.view.show_message(f"출고 실패: {error}")
            return

        self.view.show_release_result(order)
