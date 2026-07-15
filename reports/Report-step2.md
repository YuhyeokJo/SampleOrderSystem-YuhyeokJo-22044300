## Step 2 구현 리포트

### 구현 범위

- **Order 도메인 모델** (`model/order.py`): `order_id`, `sample_id`, `customer_name`, `quantity`, `status` 필드를 가진 불변(`frozen`) 데이터클래스로 정의. `Order.create_reserved(...)` 팩토리 메서드가 시료 ID/고객명/주문 수량의 형식 제약을 검증하고, 통과 시 `status`를 항상 `RESERVED`로 고정하여 반환한다. `to_dict`/`from_dict`로 JSON 직렬화를 지원한다.
- **주문번호 생성 규칙**: `OrderModel._generate_order_id()`가 날짜 제공자(`date_provider`)로부터 얻은 날짜를 `%Y%m%d`로 포맷하여 `ORD-YYYYMMDD-` 접두사를 만들고, 메모리에 로드된 기존 주문 중 같은 날짜 접두사를 가진 건수를 세어 다음 일련번호(`0001`부터, 4자리)를 계산한다. 날짜가 바뀌면 접두사가 달라지므로 자동으로 `0001`부터 다시 시작한다.
- **시료 예약(주문 접수) 기능** (`model/order_model.py`의 `reserve`): 1) `SampleModel.find_by_id`로 시료 ID 등록 여부를 확인해 없으면 `OrderValidationError` 발생, 2) `Order.create_reserved`가 고객명 비어있음/수량이 1 이상의 정수인지 검증, 3) 통과 시 주문번호를 채번하고 상태 `RESERVED`로 저장한다. `controller/order_controller.py`가 성공 시 주문번호를 포함한 메시지를, 실패 시 사유를 포함한 메시지를 출력한다.
- **JSON 파일 기반 영속성** (`model/order_repository.py`): Step 1의 `SampleRepository`와 동일하게 임시 파일(`*.tmp`)에 먼저 기록한 뒤 `os.replace`로 원자적 교체를 수행한다. 기본 저장 경로는 `data/orders.json`.
- **계층 분리**: `model/order.py`(엔티티/검증), `model/order_repository.py`(영속성), `model/order_model.py`(도메인 로직/채번), `view/order_view.py`(콘솔 입출력), `controller/order_controller.py`(메뉴 흐름 제어)로 Step 1과 동일한 패턴을 따름.
- **날짜 주입 가능한 설계**: `OrderModel.__init__`이 `date_provider`(인자 없이 호출 시 오늘 날짜를 반환하는 콜러블)를 선택적으로 주입받도록 하여, 기본값은 `datetime.date.today`이지만 테스트에서는 고정된 날짜를 반환하는 람다로 교체해 실제 시스템 날짜와 무관하게 결정적으로 검증할 수 있다.

### 생성/수정 파일 목록

- `model/order.py` (신규): `Order` 엔티티, `OrderValidationError`, `create_reserved`/`to_dict`/`from_dict`.
- `model/order_repository.py` (신규): 주문 데이터 JSON 원자적 영속성.
- `model/order_model.py` (신규): 주문 접수(`reserve`), 주문번호 채번, `all()` 조회(내부 검증/저장용, 목록 조회 메뉴는 미노출), Step 1 `SampleModel` 재사용.
- `view/order_view.py` (신규): 주문 접수 메뉴 및 입력/출력 프롬프트.
- `controller/order_controller.py` (신규): 메뉴 흐름 제어(주문 접수/종료), 입력값 정수 변환 및 실패 메시지 처리.
- `tests/test_order_model.py` (신규): 도메인 모델 단위 테스트.
- `tests/test_order_repository.py` (신규): 영속성 및 재시작 시뮬레이션 테스트.
- `tests/test_order_controller.py` (신규): 컨트롤러 흐름 테스트.
- `reports/Report-step2.md` (신규): 본 리포트.

### 작성한 테스트

**tests/test_order_model.py**
- `test_reserve_success_returns_order_with_reserved_status`: 정상 접수 시 주문번호(`ORD-20260715-0001`)·시료ID·고객명·수량·`RESERVED` 상태가 올바른지 확인.
- `test_reserve_rejects_unregistered_sample_id`: 등록되지 않은 시료 ID로 접수 시도 시 `OrderValidationError` 발생.
- `test_reserve_rejects_empty_customer_name`: 고객명이 빈 문자열이면 거부.
- `test_reserve_rejects_non_positive_quantity` (파라미터화 `0`, `-1`): 수량이 0 또는 음수면 거부.
- `test_reserve_rejects_non_integer_quantity`: 수량이 `1.5`(정수 아님)이면 거부.
- `test_reserve_allows_quantity_of_exactly_one`: 수량 `1` 경계값은 접수 허용.
- `test_reserve_generates_sequential_order_numbers_for_same_date`: 같은 날짜에 3건 연속 접수 시 일련번호가 `0001`, `0002`, `0003`으로 순서대로 증가.
- `test_reserve_resets_sequence_when_date_changes`: 날짜 제공자를 가변 리스트로 교체하여 날짜가 바뀌면 일련번호가 `0001`로 리셋되는지 확인(시스템 시계에 의존하지 않는 결정적 테스트).
- `test_all_when_no_orders_reserved_returns_empty`: 접수 이력이 없을 때 빈 리스트 반환.

**tests/test_order_repository.py**
- `test_load_all_when_file_missing_returns_empty_list`: 파일이 없을 때 빈 리스트 반환.
- `test_save_all_writes_records_and_removes_tmp_file`: 저장 후 원본 파일에 레코드가 기록되고 임시 파일이 남지 않는지 확인.
- `test_order_data_persists_after_reopening_with_new_instance`: 새 저장소/모델 인스턴스(프로세스 재시작 시뮬레이션)로 재조회 시 주문번호·시료ID·고객명·수량·상태가 그대로 유지되는지 확인.
- `test_order_data_persists_across_multiple_reservations_and_restarts`: 여러 건 접수 후 재시작해도 모든 주문번호가 유지되는지 확인.

**tests/test_order_controller.py**
- `test_reserve_flow_saves_order_and_reports_success`: 정상 입력 시 주문이 저장되고 주문번호를 포함한 성공 메시지가 출력되는지 확인.
- `test_reserve_flow_rejects_unregistered_sample_id`: 미등록 시료 ID 입력 시 주문이 저장되지 않고 실패 메시지가 출력되는지 확인.
- `test_reserve_flow_rejects_empty_customer_name`: 고객명이 빈 문자열일 때 실패 메시지 확인.
- `test_reserve_flow_rejects_non_integer_quantity`: 수량 입력값이 숫자가 아닐 때(`abc`) 실패 메시지 확인.
- `test_reserve_flow_rejects_zero_quantity`: 수량이 `0`일 때 실패 메시지 확인.
