from dataclasses import dataclass


class SampleValidationError(Exception):
    """시료 등록 시 도메인 제약을 위반했을 때 발생한다."""


@dataclass(frozen=True)
class Sample:
    sample_id: str
    name: str
    avg_production_time: float
    yield_rate: float
    stock_quantity: int

    @staticmethod
    def create(sample_id, name, avg_production_time, yield_rate, stock_quantity):
        if not isinstance(sample_id, str) or sample_id == "":
            raise SampleValidationError("시료 ID는 비어있지 않은 문자열이어야 합니다.")
        if not isinstance(name, str) or name.strip() == "":
            raise SampleValidationError("이름은 비어있지 않아야 합니다.")
        if not _is_positive_number(avg_production_time):
            raise SampleValidationError("평균 생산시간은 0보다 커야 합니다.")
        if not _is_number_in_range(yield_rate, 0.0, 1.0):
            raise SampleValidationError("수율은 0.0 이상 1.0 이하이어야 합니다.")
        if not _is_non_negative_int(stock_quantity):
            raise SampleValidationError("재고 수량은 0 이상의 정수여야 합니다.")
        return Sample(
            sample_id=sample_id,
            name=name,
            avg_production_time=float(avg_production_time),
            yield_rate=float(yield_rate),
            stock_quantity=stock_quantity,
        )

    def to_dict(self):
        return {
            "sample_id": self.sample_id,
            "name": self.name,
            "avg_production_time": self.avg_production_time,
            "yield_rate": self.yield_rate,
            "stock_quantity": self.stock_quantity,
        }

    @staticmethod
    def from_dict(data):
        return Sample(
            sample_id=data["sample_id"],
            name=data["name"],
            avg_production_time=data["avg_production_time"],
            yield_rate=data["yield_rate"],
            stock_quantity=data["stock_quantity"],
        )


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _is_positive_number(value):
    return _is_number(value) and value > 0


def _is_number_in_range(value, minimum, maximum):
    return _is_number(value) and minimum <= value <= maximum


def _is_non_negative_int(value):
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0
