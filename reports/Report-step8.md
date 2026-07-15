## Step 8 구현 리포트

### 구현 범위
- `view/console_format.py`를 신규 작성하여 `render_divider`, `render_table`, `render_status_badge`,
  `render_progress_bar`를 PRD-step8.md에 명시된 공식대로 구현했다. `render_table`은 `aligns`
  길이가 `headers`와 다르면 `ValueError`를 발생시키고, `rows`가 비어 있으면 헤더 줄만 반환한다.
- 7개 view 파일(`main_menu_view.py`, `sample_view.py`, `order_view.py`, `approval_view.py`,
  `production_view.py`, `release_view.py`, `monitoring_view.py`)을 PRD-step8.md "화면별 출력
  포맷 명세" 절 그대로 수정했다.
  - `main_menu_view.py`: `show_menu()`에 구분선+배너+메뉴, `prompt_choice()` 프롬프트를
    `"선택 > "`로 변경. `show_summary()`는 문구 변경 없음(Step 7 확정 내용 유지).
  - `sample_view.py`: `show_menu()` 개선, `show_samples()`에 건수 안내 + `render_table`
    (`aligns=["<","<",">",">",">"]`) 적용.
  - `order_view.py`: `show_menu()` 개선, 신규 `show_input_summary(sample_id, customer_name,
    quantity)`와 `show_reservation_success(order)` 추가.
  - `approval_view.py`: `show_menu()` 개선, `show_reserved_orders()`에 번호+건수+`render_table`
    (`aligns=["<","<","<","<",">",">"]`) 적용. 신규 `show_approval_result(order,
    shortage_quantity)`, `show_rejection_result(order)` 추가.
  - `production_view.py`: `show_menu()` 개선, `show_current_job()`에 `render_progress_bar` 적용,
    `show_waiting_jobs()`에 순번+건수+`render_table`(`aligns=["<","<","<",">",">",">"]`) 적용.
    신규 `show_registration_success(job)`, `show_progress_result(job, completed)` 추가.
  - `release_view.py`: `show_menu()` 개선, `show_confirmed_orders()`에 번호+건수+`render_table`
    (`aligns=["<","<","<","<",">",">"]`) 적용. 신규 `show_release_result(order)` 추가.
  - `monitoring_view.py`: `show_menu()` 개선, `show_order_counts_by_status()`에 상태 배지 적용,
    `show_sample_stock_status()`에 `render_table`(`aligns=["<","<",">",">"]`) + 상태 배지 적용.
- 5개 controller 중 PRD-step8.md에서 실제로 신규 view 결과 메서드가 정의된 4개
  (`order_controller.py`, `approval_controller.py`, `production_controller.py`,
  `release_controller.py`)만 문자열 조립 책임을 view로 위임하도록 수정했다. `sample_controller.py`는
  PRD-step8.md 화면별 명세("2. 시료 관리")에 결과 메서드가 정의되어 있지 않아(등록 성공 메시지는
  Step 7 문구 그대로 유지) 수정하지 않았다. model 호출 순서/분기 조건은 그대로 유지하고, 실패
  메시지(`f"접수 실패: {error}"` 등)도 변경하지 않았다.

### 생성/수정 파일 목록
- `view/console_format.py` (신규): 구분선/표/상태 배지/진행률 바 공통 렌더링 헬퍼
- `view/main_menu_view.py` (수정): 구분선+배너 메뉴, `"선택 > "` 프롬프트
- `view/sample_view.py` (수정): 목록 건수 안내 + `render_table` 적용
- `view/order_view.py` (수정): `show_input_summary`, `show_reservation_success` 추가
- `view/approval_view.py` (수정): 번호 포함 표, `show_approval_result`, `show_rejection_result` 추가
- `view/production_view.py` (수정): 진행률 바, 순번 포함 표, `show_registration_success`,
  `show_progress_result` 추가
- `view/release_view.py` (수정): 번호 포함 표, `show_release_result` 추가
- `view/monitoring_view.py` (수정): 상태 배지 적용
- `controller/order_controller.py` (수정): `show_input_summary`/`show_reservation_success` 호출로 교체
- `controller/approval_controller.py` (수정): `show_approval_result`/`show_rejection_result` 호출로 교체
- `controller/production_controller.py` (수정): `show_registration_success`/`show_progress_result` 호출로 교체
- `controller/release_controller.py` (수정): `show_release_result` 호출로 교체
- `tests/test_console_format.py` (신규): 공통 헬퍼 단위 테스트
- `tests/test_main_menu_view.py`, `tests/test_sample_view.py`, `tests/test_order_view.py`,
  `tests/test_approval_view.py`, `tests/test_production_view.py`, `tests/test_release_view.py`,
  `tests/test_monitoring_view.py` (신규): 각 view 출력 포맷 검증(capsys)
- `tests/test_order_controller.py`, `tests/test_approval_controller.py`,
  `tests/test_production_controller.py`, `tests/test_release_controller.py` (수정): FakeView에
  신규 메서드 추가, `show_message` 텍스트 검사 assertion을 새 view 메서드 호출/인자 검사로 변경

### 작성한 테스트
- `tests/test_console_format.py`: `render_divider` 기본/커스텀 폭, `render_table`의 빈 rows
  헤더만 반환, 좌/우 정렬, 데이터 길이에 따른 컬럼 폭 확장, `aligns` 길이 불일치 시 `ValueError`,
  `render_status_badge` 대괄호 감싸기, `render_progress_bar`의 `total=0`/`current=0`/
  `current=total`/중간 비율 경계값 검증.
- `tests/test_main_menu_view.py`: `show_menu()`의 구분선/배너/메뉴 항목 출력, `show_summary()`의
  0건/N건 문구 유지, `prompt_choice()`의 `"선택 > "` 프롬프트 검증.
- `tests/test_sample_view.py`: `show_samples()` 빈 목록 문구, 건수 안내 및 표 헤더/데이터 출력 검증.
- `tests/test_order_view.py`: `show_input_summary`/`show_reservation_success`의 출력 형식 검증.
- `tests/test_approval_view.py`: `show_reserved_orders()` 빈 목록/번호 포함 표,
  `show_approval_result()`의 재고 충분/부족 두 경우, `show_rejection_result()` 검증.
- `tests/test_production_view.py`: `show_current_job()` 빈 상태/진행률 바 출력,
  `show_waiting_jobs()` 빈 목록/순번 포함 표, `show_registration_success()`,
  `show_progress_result()`의 완료/미완료 두 경우 검증.
- `tests/test_release_view.py`: `show_confirmed_orders()` 빈 목록/번호 포함 표,
  `show_release_result()` 상태 전이 출력 검증.
- `tests/test_monitoring_view.py`: `show_order_counts_by_status()`의 상태 배지 출력,
  `show_sample_stock_status()` 빈 목록 문구 및 상태 배지 포함 표 검증.
- 기존 controller 테스트(`test_order_controller.py`, `test_approval_controller.py`,
  `test_production_controller.py`, `test_release_controller.py`)는 FakeView에 신규 메서드를
  추가하고, 결과 검증 assertion을 "어떤 view 메서드가 어떤 도메인 객체/인자로 호출되었는가"로
  변경했다(model 호출 검증은 기존과 동일하게 유지).
- 전체 `pytest` 실행 결과 192개 테스트 모두 통과(개발 중 직접 실행 확인, 최종 검증은
  test-verifier가 별도 수행 예정).
