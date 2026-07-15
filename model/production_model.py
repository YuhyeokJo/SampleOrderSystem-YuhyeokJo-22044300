import math

from model.order_model import OrderModel
from model.production_job import ProductionJob, ProductionValidationError
from model.production_repository import ProductionRepository
from model.sample_model import SampleModel

DEFAULT_STORAGE_PATH = "data/production_jobs.json"
YIELD_EFFICIENCY_FACTOR = 0.9
PRODUCING_STATUS = "PRODUCING"
CONFIRMED_STATUS = "CONFIRMED"


class ProductionModel:
    """생산 큐 등록, 진행 기록, 완료 처리와 현황 조회를 담당하는 도메인 모델."""

    def __init__(self, repository=None, sample_model=None, order_model=None):
        self._repository = repository or ProductionRepository(DEFAULT_STORAGE_PATH)
        self._sample_model = sample_model or SampleModel()
        self._order_model = order_model or OrderModel()
        self._queue = [ProductionJob.from_dict(record) for record in self._repository.load_all()]
        self._sequence_counter = max((job.sequence for job in self._queue), default=0)

    def register(self, order_id, sample_id, shortage_quantity):
        sample = self._sample_model.find_by_id(sample_id)
        if sample is None:
            raise ProductionValidationError(f"시료 ID '{sample_id}'는 등록되어 있지 않습니다.")
        if not _is_positive_int(shortage_quantity):
            raise ProductionValidationError("부족분은 1 이상의 정수여야 합니다.")
        if sample.yield_rate == 0.0:
            raise ProductionValidationError("수율이 0인 시료는 생산할 수 없습니다.")

        actual_production_quantity = math.ceil(
            shortage_quantity / (sample.yield_rate * YIELD_EFFICIENCY_FACTOR)
        )
        total_production_time = sample.avg_production_time * actual_production_quantity
        self._sequence_counter += 1
        job = ProductionJob.create(
            order_id=order_id,
            sample_id=sample_id,
            shortage_quantity=shortage_quantity,
            actual_production_quantity=actual_production_quantity,
            total_production_time=total_production_time,
            sequence=self._sequence_counter,
        )
        self._queue.append(job)
        self._save()
        return job

    def record_progress(self, produced_quantity):
        if not self._queue:
            raise ProductionValidationError("진행 중인 생산 항목이 없습니다.")
        if not _is_positive_int(produced_quantity):
            raise ProductionValidationError("생산 수량은 1 이상의 정수여야 합니다.")

        current_job = self._queue[0]
        current_job.add_produced_quantity(produced_quantity)

        if current_job.is_complete():
            self._complete_current_job()
            return current_job, True

        self._save()
        return current_job, False

    def current_job(self):
        return self._queue[0] if self._queue else None

    def waiting_jobs(self):
        return list(self._queue[1:])

    def _complete_current_job(self):
        job = self._queue[0]
        order = self._order_model.find_by_id(job.order_id)
        if order is None or order.status != PRODUCING_STATUS:
            self._save()
            raise ProductionValidationError(
                f"주문 '{job.order_id}'의 상태가 PRODUCING이 아니어서 생산 완료 처리를 중단합니다."
            )
        self._order_model.update_status(job.order_id, CONFIRMED_STATUS)
        self._queue.pop(0)
        self._save()

    def _save(self):
        self._repository.save_all([job.to_dict() for job in self._queue])


def _is_positive_int(value):
    return isinstance(value, int) and not isinstance(value, bool) and value >= 1
