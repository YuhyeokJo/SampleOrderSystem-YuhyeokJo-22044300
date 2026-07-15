## Step 1 구현 리포트

### 구현 범위
- Sample 도메인 모델: `sample_id`(문자열, 고유), `name`(비어있지 않은 문자열), `avg_production_time`(0보다 큰 숫자), `yield_rate`(0.0~1.0 소수), `stock_quantity`(0 이상 정수) 필드를 가진 불변 `Sample` 엔티티로 구현. `Sample.create()`에서 도메인 제약을 모두 검증하고 위반 시 `SampleValidationError`를 발생시킨다.
- 시료 등록: `SampleModel.register()`가 시료 ID 중복(정규화 없이 문자열 그대로 비교) 여부를 먼저 확인한 뒤 `Sample.create()`로 필드 제약을 검증한다. 하나라도 위반하면 등록을 거부하고 사유를 담은 예외를 발생시키며, 컨트롤러가 이를 받아 "등록 실패: <사유>" 메시지로 안내한다.
- 시료 목록 조회: `SampleModel.all()`이 등록된 전체 시료를 반환하고, `SampleView.show_samples()`가 ID/이름/평균 생산시간/수율/재고 수량을 표 형태로 출력한다. 목록이 비어 있으면 "등록된 시료가 없습니다." 안내.
- 시료 검색: `SampleModel.search_by_name(keyword)`가 이름에 검색어가 포함된 시료만 반환하며, 결과가 없으면 "일치하는 시료가 없습니다." 안내.
- JSON 파일 기반 영속성: `SampleRepository`가 `save_all()` 시 임시 파일(`<path>.tmp`)에 먼저 기록한 뒤 `os.replace()`로 원자적 교체를 수행한다. `SampleModel`은 생성 시 저장소에서 기존 레코드를 불러와 메모리 상태를 복원하므로, 프로세스를 재시작해 새 `SampleModel` 인스턴스를 만들어도 이전 데이터가 유지된다.
- 계층 분리: `model/`은 데이터와 검증/영속 로직만 담당하고 콘솔 입출력을 포함하지 않는다. `view/`는 입력값을 그대로 문자열로 반환하고 출력 형식만 다루며 비즈니스 로직을 포함하지 않는다. `controller/`가 입력 파싱(문자열→숫자 변환)과 model/view 호출 순서를 조정한다.

### 생성/수정 파일 목록
- `model/__init__.py`, `view/__init__.py`, `controller/__init__.py`: 패키지 초기화 파일(신규).
- `conftest.py`: 프로젝트 루트를 pytest 수집 시 `sys.path`에 포함시키기 위한 빈 설정 파일(신규).
- `model/sample.py`: `Sample` 엔티티와 `SampleValidationError`, 필드 검증 로직(신규).
- `model/sample_repository.py`: JSON 파일 기반 영속성, 임시 파일 작성 후 `os.replace` 원자적 교체(신규).
- `model/sample_model.py`: 시료 등록/조회/검색 비즈니스 로직, `SampleRepository`를 사용해 초기화 시 데이터 복원(신규).
- `view/sample_view.py`: 시료 관리 메뉴/입력 프롬프트/결과 출력 등 콘솔 입출력(신규).
- `controller/sample_controller.py`: 메뉴 흐름 제어, 입력값 파싱, model 호출 및 결과 안내(신규).
- `main.py`: `SampleController`를 실행하는 진입점(신규).
- `tests/test_sample_model.py`: 등록/조회/검색 단위 테스트(신규).
- `tests/test_sample_repository.py`: 저장소 영속성 단위 테스트(신규).
- `tests/test_sample_controller.py`: 컨트롤러 흐름 단위 테스트(신규).
- `reports/Report-step1.md`: 본 리포트(신규).

### 작성한 테스트
- `tests/test_sample_model.py`
  - `test_register_success_returns_sample_with_given_values`: 정상 등록 시 값이 그대로 반영되는지 확인.
  - `test_register_duplicate_id_is_rejected`: 중복 ID 등록 거부.
  - `test_register_duplicate_id_uses_exact_string_comparison`: `"1"`과 `"01"`을 서로 다른 ID로 취급해 등록 허용(정규화 없는 문자열 비교 확인).
  - `test_register_rejects_non_positive_avg_production_time`: 평균 생산시간이 0 또는 음수일 때 거부(파라미터화: 0, -1, -0.5).
  - `test_register_rejects_yield_rate_out_of_range`: 수율이 0.0 미만/1.0 초과일 때 거부.
  - `test_register_allows_yield_rate_boundary_values`: 수율이 정확히 0.0/1.0일 때 허용.
  - `test_register_rejects_invalid_stock_quantity`: 재고 수량이 음수/비정수(float, 문자열)일 때 거부.
  - `test_register_allows_zero_stock_quantity`: 재고 수량이 정확히 0일 때 허용.
  - `test_register_rejects_empty_name`: 공백만 있는 이름 거부.
  - `test_list_when_no_samples_registered_returns_empty`: 시료가 없을 때 목록 조회가 빈 리스트를 반환.
  - `test_search_when_no_samples_registered_returns_empty`: 시료가 없을 때 검색이 빈 리스트를 반환.
  - `test_search_by_name_returns_matching_samples`: 이름에 검색어가 포함된 시료만 반환.
  - `test_search_with_no_matching_keyword_returns_empty`: 검색어와 일치하는 시료가 없을 때 빈 리스트 반환.
- `tests/test_sample_repository.py`
  - `test_load_all_when_file_missing_returns_empty_list`: 파일이 없을 때 빈 목록 반환.
  - `test_save_all_writes_records_and_removes_tmp_file`: 저장 후 파일 내용이 올바르고 임시 파일이 남지 않음을 확인.
  - `test_data_persists_after_reopening_with_new_instance`: 시료 1건 등록 후 새 `SampleModel`/`SampleRepository` 인스턴스(프로세스 재시작 시뮬레이션)로 재오픈 시 데이터가 그대로 유지되는지 확인.
  - `test_data_persists_across_multiple_registrations_and_restarts`: 여러 건 등록 후 재시작 시뮬레이션에서도 전체 데이터 유지 확인.
- `tests/test_sample_controller.py`
  - `test_register_flow_saves_sample_and_reports_success`: 등록 메뉴 흐름에서 시료가 저장되고 성공 메시지가 출력되는지 확인.
  - `test_register_flow_reports_failure_on_invalid_input`: 동일 ID로 두 번 등록 시도 시 실패 메시지 출력 확인.
  - `test_list_flow_with_no_samples_shows_empty_result`: 시료 없음 상태에서 목록 조회 흐름이 빈 결과를 view에 전달하는지 확인.
  - `test_search_flow_with_no_match_reports_not_found`: 검색 결과가 없을 때 안내 메시지 출력 확인.

테스트는 작성만 하였으며, 실행 검증은 test-verifier가 수행한다.
