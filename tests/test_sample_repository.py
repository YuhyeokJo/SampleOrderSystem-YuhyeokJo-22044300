import json
import os

from model.sample_model import SampleModel
from model.sample_repository import SampleRepository


def test_load_all_when_file_missing_returns_empty_list(tmp_path):
    repository = SampleRepository(str(tmp_path / "samples.json"))

    assert repository.load_all() == []


def test_save_all_writes_records_and_removes_tmp_file(tmp_path):
    file_path = tmp_path / "samples.json"
    repository = SampleRepository(str(file_path))
    records = [{"sample_id": "S-1", "name": "Wafer-A"}]

    repository.save_all(records)

    assert file_path.exists()
    assert not (tmp_path / "samples.json.tmp").exists()
    assert json.loads(file_path.read_text(encoding="utf-8")) == records


def test_data_persists_after_reopening_with_new_instance(tmp_path):
    file_path = str(tmp_path / "samples.json")

    first_process_model = SampleModel(repository=SampleRepository(file_path))
    first_process_model.register("S-1", "Wafer-A", 10.0, 0.9, 100)

    restarted_process_model = SampleModel(repository=SampleRepository(file_path))
    restarted_samples = restarted_process_model.all()

    assert len(restarted_samples) == 1
    assert restarted_samples[0].sample_id == "S-1"
    assert restarted_samples[0].name == "Wafer-A"
    assert restarted_samples[0].avg_production_time == 10.0
    assert restarted_samples[0].yield_rate == 0.9
    assert restarted_samples[0].stock_quantity == 100


def test_data_persists_across_multiple_registrations_and_restarts(tmp_path):
    file_path = str(tmp_path / "samples.json")

    model_before_restart = SampleModel(repository=SampleRepository(file_path))
    model_before_restart.register("S-1", "Wafer-A", 10.0, 0.9, 100)
    model_before_restart.register("S-2", "Wafer-B", 5.0, 0.5, 10)

    model_after_restart = SampleModel(repository=SampleRepository(file_path))

    assert {sample.sample_id for sample in model_after_restart.all()} == {"S-1", "S-2"}
