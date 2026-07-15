from model.order import OrderValidationError
from model.order_model import OrderModel
from view.order_view import OrderView


class OrderController:
    """시료 주문 접수 메뉴의 흐름을 제어한다."""

    def __init__(self, model=None, view=None):
        self.model = model or OrderModel()
        self.view = view or OrderView()

    def run(self):
        actions = {
            "1": self._reserve_order,
        }
        while True:
            self.view.show_menu()
            choice = self.view.prompt_choice()
            if choice == "2":
                self.view.show_message("종료합니다.")
                break
            action = actions.get(choice)
            if action is None:
                self.view.show_message("올바르지 않은 선택입니다.")
                continue
            action()

    def _reserve_order(self):
        sample_id = self.view.prompt_sample_id()
        customer_name = self.view.prompt_customer_name()
        raw_quantity = self.view.prompt_quantity()

        try:
            quantity = int(raw_quantity)
        except ValueError:
            self.view.show_message("접수 실패: 주문 수량은 정수여야 합니다.")
            return

        try:
            order = self.model.reserve(sample_id, customer_name, quantity)
        except OrderValidationError as error:
            self.view.show_message(f"접수 실패: {error}")
            return
        self.view.show_message(f"접수 완료: 주문번호 {order.order_id}")
