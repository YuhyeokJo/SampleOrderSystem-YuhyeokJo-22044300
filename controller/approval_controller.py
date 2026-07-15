from model.approval_model import ApprovalModel
from model.order import OrderValidationError
from model.production_job import ProductionValidationError
from model.sample import SampleValidationError
from view.approval_view import ApprovalView

APPROVAL_ERROR_TYPES = (OrderValidationError, ProductionValidationError, SampleValidationError)


class ApprovalController:
    """주문 승인/거절 메뉴의 흐름을 제어한다."""

    def __init__(self, model=None, view=None):
        self.model = model or ApprovalModel()
        self.view = view or ApprovalView()

    def run(self):
        actions = {
            "1": self._show_reserved_orders,
            "2": self._approve_order,
            "3": self._reject_order,
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

    def _show_reserved_orders(self):
        orders = self.model.list_reserved()
        self.view.show_reserved_orders(orders)

    def _approve_order(self):
        order_id = self.view.prompt_order_id()

        try:
            order, shortage_quantity = self.model.approve(order_id)
        except APPROVAL_ERROR_TYPES as error:
            self.view.show_message(f"승인 실패: {error}")
            return

        if shortage_quantity is None:
            self.view.show_message(f"승인 완료: 주문번호 {order.order_id}, 상태 CONFIRMED로 전환")
        else:
            self.view.show_message(
                f"승인 완료: 주문번호 {order.order_id}, 상태 PRODUCING으로 전환, "
                f"부족분 {shortage_quantity} 생산라인 등록"
            )

    def _reject_order(self):
        order_id = self.view.prompt_order_id()

        try:
            order = self.model.reject(order_id)
        except OrderValidationError as error:
            self.view.show_message(f"거절 실패: {error}")
            return

        self.view.show_message(f"거절 완료: 주문번호 {order.order_id}, 상태 REJECTED로 전환")
