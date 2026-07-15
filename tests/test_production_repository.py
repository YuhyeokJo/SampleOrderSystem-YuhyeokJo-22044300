import json

from model.production_repository import ProductionRepository


def test_load_all_when_file_missing_returns_empty_list(tmp_path):
    repository = ProductionRepository(str(tmp_path / "production_jobs.json"))

    assert repository.load_all() == []


def test_save_all_writes_records_and_removes_tmp_file(tmp_path):
    file_path = tmp_path / "production_jobs.json"
    repository = ProductionRepository(str(file_path))
    records = [{"order_id": "ORD-1", "sample_id": "S-1", "produced_quantity": 0}]

    repository.save_all(records)

    assert file_path.exists()
    assert not (tmp_path / "production_jobs.json.tmp").exists()
    assert json.loads(file_path.read_text(encoding="utf-8")) == records


def test_save_all_overwrites_previous_content(tmp_path):
    file_path = tmp_path / "production_jobs.json"
    repository = ProductionRepository(str(file_path))

    repository.save_all([{"order_id": "ORD-1"}])
    repository.save_all([{"order_id": "ORD-2"}])

    assert json.loads(file_path.read_text(encoding="utf-8")) == [{"order_id": "ORD-2"}]
