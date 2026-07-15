from model.order import OrderValidationError
from model.order_model import OrderModel
from model.production_model import ProductionModel
from model.sample_model import SampleModel

RESERVED_STATUS = "RESERVED"
CONFIRMED_STATUS = "CONFIRMED"
PRODUCING_STATUS = "PRODUCING"
REJECTED_STATUS = "REJECTED"


class ApprovalModel:
    """접수된(RESERVED) 주문의 승인/거절 처리를 담당하는 도메인 모델."""

    def __init__(self, order_model=None, sample_model=None, production_model=None):
        self._order_model = order_model or OrderModel()
        self._sample_model = sample_model or SampleModel()
        self._production_model = production_model or ProductionModel()

    def list_reserved(self):
        return self._order_model.list_reserved()

    def approve(self, order_id):
        order = self._require_reserved_order(order_id)
        sample = self._sample_model.find_by_id(order.sample_id)
        if sample is None:
            raise OrderValidationError(f"시료 ID '{order.sample_id}'는 등록되어 있지 않습니다.")

        if sample.stock_quantity >= order.quantity:
            self._sample_model.decrease_stock(order.sample_id, order.quantity)
            updated_order = self._order_model.update_status(order_id, CONFIRMED_STATUS)
            return updated_order, None

        shortage_quantity = order.quantity - sample.stock_quantity
        self._production_model.register(order_id, order.sample_id, shortage_quantity)
        self._sample_model.decrease_stock(order.sample_id, sample.stock_quantity)
        updated_order = self._order_model.update_status(order_id, PRODUCING_STATUS)
        return updated_order, shortage_quantity

    def reject(self, order_id):
        self._require_reserved_order(order_id)
        return self._order_model.update_status(order_id, REJECTED_STATUS)

    def _require_reserved_order(self, order_id):
        order = self._order_model.find_by_id(order_id)
        if order is None:
            raise OrderValidationError(f"주문번호 '{order_id}'는 존재하지 않습니다.")
        if order.status != RESERVED_STATUS:
            raise OrderValidationError(f"주문번호 '{order_id}'는 RESERVED 상태가 아니어서 처리할 수 없습니다.")
        return order
