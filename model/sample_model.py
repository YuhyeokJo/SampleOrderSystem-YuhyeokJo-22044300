from model.sample import Sample, SampleValidationError
from model.sample_repository import SampleRepository

DEFAULT_STORAGE_PATH = "data/samples.json"


class SampleModel:
    """시료 등록/목록 조회/검색을 담당하는 도메인 모델."""

    def __init__(self, repository=None):
        self._repository = repository or SampleRepository(DEFAULT_STORAGE_PATH)
        self._samples = [Sample.from_dict(record) for record in self._repository.load_all()]

    def register(self, sample_id, name, avg_production_time, yield_rate, stock_quantity):
        if self.find_by_id(sample_id) is not None:
            raise SampleValidationError(f"시료 ID '{sample_id}'는 이미 등록되어 있습니다.")
        sample = Sample.create(sample_id, name, avg_production_time, yield_rate, stock_quantity)
        self._samples.append(sample)
        self._save()
        return sample

    def find_by_id(self, sample_id):
        for sample in self._samples:
            if sample.sample_id == sample_id:
                return sample
        return None

    def all(self):
        return list(self._samples)

    def search_by_name(self, keyword):
        return [sample for sample in self._samples if keyword in sample.name]

    def _save(self):
        self._repository.save_all([sample.to_dict() for sample in self._samples])
