from datetime import date

from model.order import RESERVED_STATUS, Order, OrderValidationError
from model.order_repository import OrderRepository
from model.sample_model import SampleModel

DEFAULT_STORAGE_PATH = "data/orders.json"
ORDER_NUMBER_DATE_FORMAT = "%Y%m%d"
ORDER_NUMBER_SEQUENCE_DIGITS = 4


class OrderModel:
    """시료 주문 접수를 담당하는 도메인 모델."""

    def __init__(self, repository=None, sample_model=None, date_provider=None):
        self._repository = repository or OrderRepository(DEFAULT_STORAGE_PATH)
        self._sample_model = sample_model or SampleModel()
        self._date_provider = date_provider or date.today
        self._orders = [Order.from_dict(record) for record in self._repository.load_all()]

    def reserve(self, sample_id, customer_name, quantity):
        if self._sample_model.find_by_id(sample_id) is None:
            raise OrderValidationError(f"시료 ID '{sample_id}'는 등록되어 있지 않습니다.")
        order_id = self._generate_order_id()
        order = Order.create_reserved(order_id, sample_id, customer_name, quantity)
        self._orders.append(order)
        self._save()
        return order

    def all(self):
        return list(self._orders)

    def find_by_id(self, order_id):
        for order in self._orders:
            if order.order_id == order_id:
                return order
        return None

    def list_reserved(self):
        return [order for order in self._orders if order.status == RESERVED_STATUS]

    def update_status(self, order_id, new_status):
        index = self._index_of(order_id)
        if index is None:
            raise OrderValidationError(f"주문번호 '{order_id}'는 존재하지 않습니다.")
        updated_order = self._orders[index].with_status(new_status)
        self._orders[index] = updated_order
        self._save()
        return updated_order

    def _index_of(self, order_id):
        for index, order in enumerate(self._orders):
            if order.order_id == order_id:
                return index
        return None

    def _generate_order_id(self):
        today_str = self._date_provider().strftime(ORDER_NUMBER_DATE_FORMAT)
        prefix = f"ORD-{today_str}-"
        existing_count = sum(1 for order in self._orders if order.order_id.startswith(prefix))
        sequence = str(existing_count + 1).zfill(ORDER_NUMBER_SEQUENCE_DIGITS)
        return f"{prefix}{sequence}"

    def _save(self):
        self._repository.save_all([order.to_dict() for order in self._orders])
