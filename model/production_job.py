from dataclasses import dataclass


class ProductionValidationError(Exception):
    """생산 항목 등록/처리 시 도메인 제약을 위반했을 때 발생한다."""


@dataclass
class ProductionJob:
    order_id: str
    sample_id: str
    shortage_quantity: int
    actual_production_quantity: int
    total_production_time: float
    sequence: int
    produced_quantity: int = 0

    @staticmethod
    def create(
        order_id,
        sample_id,
        shortage_quantity,
        actual_production_quantity,
        total_production_time,
        sequence,
    ):
        if not isinstance(order_id, str) or order_id == "":
            raise ProductionValidationError("주문번호는 비어있지 않은 문자열이어야 합니다.")
        if not isinstance(sample_id, str) or sample_id == "":
            raise ProductionValidationError("시료 ID는 비어있지 않은 문자열이어야 합니다.")
        if not _is_positive_int(shortage_quantity):
            raise ProductionValidationError("부족분은 1 이상의 정수여야 합니다.")
        return ProductionJob(
            order_id=order_id,
            sample_id=sample_id,
            shortage_quantity=shortage_quantity,
            actual_production_quantity=actual_production_quantity,
            total_production_time=total_production_time,
            sequence=sequence,
            produced_quantity=0,
        )

    def add_produced_quantity(self, amount):
        self.produced_quantity = min(self.produced_quantity + amount, self.actual_production_quantity)

    def is_complete(self):
        return self.produced_quantity >= self.actual_production_quantity

    def to_dict(self):
        return {
            "order_id": self.order_id,
            "sample_id": self.sample_id,
            "shortage_quantity": self.shortage_quantity,
            "actual_production_quantity": self.actual_production_quantity,
            "total_production_time": self.total_production_time,
            "sequence": self.sequence,
            "produced_quantity": self.produced_quantity,
        }

    @staticmethod
    def from_dict(data):
        return ProductionJob(
            order_id=data["order_id"],
            sample_id=data["sample_id"],
            shortage_quantity=data["shortage_quantity"],
            actual_production_quantity=data["actual_production_quantity"],
            total_production_time=data["total_production_time"],
            sequence=data["sequence"],
            produced_quantity=data["produced_quantity"],
        )


def _is_positive_int(value):
    return isinstance(value, int) and not isinstance(value, bool) and value >= 1
