from dataclasses import dataclass, replace

RESERVED_STATUS = "RESERVED"


class OrderValidationError(Exception):
    """주문 접수 시 도메인 제약을 위반했을 때 발생한다."""


@dataclass(frozen=True)
class Order:
    order_id: str
    sample_id: str
    customer_name: str
    quantity: int
    status: str

    @staticmethod
    def create_reserved(order_id, sample_id, customer_name, quantity):
        if not isinstance(order_id, str) or order_id == "":
            raise OrderValidationError("주문번호는 비어있지 않은 문자열이어야 합니다.")
        if not isinstance(sample_id, str) or sample_id == "":
            raise OrderValidationError("시료 ID는 비어있지 않은 문자열이어야 합니다.")
        if not isinstance(customer_name, str) or customer_name.strip() == "":
            raise OrderValidationError("고객명은 비어있지 않아야 합니다.")
        if not _is_positive_int(quantity):
            raise OrderValidationError("주문 수량은 1 이상의 정수여야 합니다.")
        return Order(
            order_id=order_id,
            sample_id=sample_id,
            customer_name=customer_name,
            quantity=quantity,
            status=RESERVED_STATUS,
        )

    def with_status(self, new_status):
        return replace(self, status=new_status)

    def to_dict(self):
        return {
            "order_id": self.order_id,
            "sample_id": self.sample_id,
            "customer_name": self.customer_name,
            "quantity": self.quantity,
            "status": self.status,
        }

    @staticmethod
    def from_dict(data):
        return Order(
            order_id=data["order_id"],
            sample_id=data["sample_id"],
            customer_name=data["customer_name"],
            quantity=data["quantity"],
            status=data["status"],
        )


def _is_positive_int(value):
    return isinstance(value, int) and not isinstance(value, bool) and value >= 1
