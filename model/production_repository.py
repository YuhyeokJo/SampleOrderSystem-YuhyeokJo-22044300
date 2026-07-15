import json
import os


class ProductionRepository:
    """생산 큐 데이터를 JSON 파일로 영속화한다.

    저장 시 임시 파일에 먼저 기록한 뒤 os.replace로 원본 파일을 원자적으로
    교체하여, 쓰기 도중 오류가 발생해도 기존 파일이 손상되지 않도록 한다.
    """

    def __init__(self, file_path):
        self._file_path = file_path

    def load_all(self):
        if not os.path.exists(self._file_path):
            return []
        with open(self._file_path, "r", encoding="utf-8") as file:
            content = file.read()
        if not content.strip():
            return []
        return json.loads(content)

    def save_all(self, records):
        directory = os.path.dirname(self._file_path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        tmp_path = f"{self._file_path}.tmp"
        with open(tmp_path, "w", encoding="utf-8") as file:
            json.dump(records, file, ensure_ascii=False, indent=2)
        os.replace(tmp_path, self._file_path)
