from model.order import OrderValidationError
from model.order_model import OrderModel

CONFIRMED_STATUS = "CONFIRMED"
RELEASE_STATUS = "RELEASE"


class ReleaseModel:
    """승인 완료된(CONFIRMED) 주문의 출고 처리를 담당하는 도메인 모델."""

    def __init__(self, order_model=None):
        self._order_model = order_model or OrderModel()

    def list_confirmed(self):
        return self._order_model.list_confirmed()

    def release(self, order_id):
        order = self._order_model.find_by_id(order_id)
        if order is None:
            raise OrderValidationError(f"주문번호 '{order_id}'는 존재하지 않습니다.")
        if order.status != CONFIRMED_STATUS:
            raise OrderValidationError(f"주문번호 '{order_id}'는 CONFIRMED 상태가 아니어서 출고할 수 없습니다.")
        return self._order_model.update_status(order_id, RELEASE_STATUS)
