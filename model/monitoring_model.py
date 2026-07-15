from model.sample_model import SampleModel
from model.order_model import OrderModel

RESERVED_STATUS = "RESERVED"
CONFIRMED_STATUS = "CONFIRMED"
PRODUCING_STATUS = "PRODUCING"
RELEASE_STATUS = "RELEASE"

MONITORED_ORDER_STATUSES = (RESERVED_STATUS, CONFIRMED_STATUS, PRODUCING_STATUS, RELEASE_STATUS)

DEPLETED = "고갈"
SUFFICIENT = "여유"
SHORTAGE = "부족"


class MonitoringModel:
    """주문 현황과 시료 재고 현황을 조회·집계하는 읽기 전용 모델."""

    def __init__(self, sample_model=None, order_model=None):
        self._sample_model = sample_model or SampleModel()
        self._order_model = order_model or OrderModel()

    def count_orders_by_status(self):
        counts = {status: 0 for status in MONITORED_ORDER_STATUSES}
        for order in self._order_model.all():
            if order.status in counts:
                counts[order.status] += 1
        return counts

    def sample_stock_status(self):
        reserved_orders = self._order_model.list_reserved()
        return [
            {
                "sample_id": sample.sample_id,
                "name": sample.name,
                "stock_quantity": sample.stock_quantity,
                "status": self._judge_status(sample, reserved_orders),
            }
            for sample in self._sample_model.all()
        ]

    def _judge_status(self, sample, reserved_orders):
        if sample.stock_quantity == 0:
            return DEPLETED
        demand = sum(order.quantity for order in reserved_orders if order.sample_id == sample.sample_id)
        return SUFFICIENT if sample.stock_quantity >= demand else SHORTAGE
