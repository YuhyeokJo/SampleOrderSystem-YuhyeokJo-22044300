## Step 3 구현 리포트

### 구현 범위

- **`OrderModel` 확장** (`model/order_model.py`, `model/order.py`)
  - `Order`에 `with_status(new_status)`를 추가하여 상태가 변경된 새 `Order` 인스턴스를 생성한다(`dataclasses.replace` 사용).
  - `OrderModel`에 `find_by_id(order_id)`와 `update_status(order_id, new_status)`를 추가했다. `update_status`는 대상 주문이 없으면 `OrderValidationError`를 발생시키고, 있으면 상태를 갱신한 뒤 재저장한다. 상태값의 종류나 전이 규칙은 검증하지 않는다(PRD/Plan 명시대로 호출자 책임).

- **`ProductionJob` 도메인 모델** (`model/production_job.py`)
  - 필드: `order_id`, `sample_id`, `shortage_quantity`(부족분), `actual_production_quantity`(실 생산량), `total_production_time`(총 생산 시간), `sequence`(등록 순서), `produced_quantity`(누적 생산량, 초기 0).
  - `create(...)` 생성자에서 주문번호/시료 ID 비어있지 않은 문자열, 부족분 1 이상 정수를 검증한다(실 생산량/총 생산 시간은 이미 계산되어 전달됨을 전제로 그대로 저장).
  - `add_produced_quantity(amount)`는 누적 생산량을 더하되 실 생산량을 초과하지 않도록 `min`으로 캡핑한다.
  - `is_complete()`로 완료 여부를 판단한다.
  - `to_dict`/`from_dict`로 JSON 직렬화를 지원한다.

- **생산량 계산 및 생산 큐 등록** (`model/production_model.py`, `ProductionModel.register`)
  - 시료 ID를 `SampleModel.find_by_id`로 조회하여 없으면 거부, 부족분이 1 이상 정수가 아니면 거부, 시료의 `yield_rate`가 정확히 `0.0`이면 "수율이 0인 시료는 생산할 수 없습니다" 사유로 거부(0 나눗셈 방지)한다.
  - 통과하면 `actual_production_quantity = ceil(shortage_quantity / (yield_rate * 0.9))`, `total_production_time = avg_production_time * actual_production_quantity`를 계산하고, 내부 시퀀스 카운터를 증가시켜 `ProductionJob`을 생성한 뒤 큐(list) 맨 뒤에 추가(FIFO)하고 저장한다.

- **생산 진행 기록** (`ProductionModel.record_progress`)
  - 큐가 비어 있으면 거부. 큐 맨 앞(진행 중 항목)의 `produced_quantity`에 입력값을 누적하되 실 생산량을 넘지 않도록 캡핑한다.
  - 누적값이 실 생산량에 도달하면 완료 처리(`_complete_current_job`)를 자동 수행하고, `(job, True)`를 반환한다. 미도달 시 저장 후 `(job, False)`를 반환한다.

- **생산 완료 처리** (`ProductionModel._complete_current_job`)
  - 대상 주문을 `OrderModel.find_by_id`로 조회하여 상태가 `PRODUCING`이 아니면(또는 주문이 없으면) 큐 변경 없이 `ProductionValidationError`를 발생시켜 처리를 중단한다(단, 이미 누적된 `produced_quantity`는 유지·저장된다).
  - `PRODUCING`이면 `OrderModel.update_status(order_id, "CONFIRMED")`로 전환하고, 완료된 항목을 큐에서 제거한 뒤 저장한다. 다음 대기 항목이 있으면 그대로 큐의 새 맨 앞(진행 중)이 되며 `produced_quantity`는 0에서 시작한다(별도 초기화 불필요, 원래 0으로 등록됨).

- **생산 현황 조회 / 대기 주문 확인** (`ProductionModel.current_job`, `ProductionModel.waiting_jobs`)
  - `current_job()`은 큐 맨 앞(없으면 `None`)을 반환하고, `waiting_jobs()`는 맨 앞을 제외한 나머지를 FIFO 순서 그대로 반환한다.

- **JSON 파일 기반 영속성** (`model/production_repository.py`)
  - Step 1/2의 `SampleRepository`/`OrderRepository`와 동일하게 임시 파일 작성 후 `os.replace`로 원자적 교체하는 패턴을 그대로 적용했다. 기본 저장 경로는 `data/production_jobs.json`.

- **콘솔 입출력 / 흐름 제어** (`view/production_view.py`, `controller/production_controller.py`)
  - 메뉴: 1) 생산 큐 등록, 2) 생산 진행 기록, 3) 생산 현황 조회, 4) 대기 주문 확인, 5) 종료. Step 1/2와 동일한 model/view/controller 계층 분리 패턴을 따른다.
  - 등록/진행 기록 실패 시 `ProductionValidationError` 메시지를 그대로 안내하고, 완료 시 "생산 완료: 주문번호 ..., 상태 CONFIRMED로 전환" 메시지를 출력한다.

### 생성/수정 파일 목록

- `model/order.py` (수정): `Order.with_status(new_status)` 추가.
- `model/order_model.py` (수정): `find_by_id`, `update_status` 추가.
- `model/production_job.py` (신규): `ProductionJob` 엔티티, `ProductionValidationError`.
- `model/production_repository.py` (신규): 생산 큐 JSON 영속성(원자적 저장).
- `model/production_model.py` (신규): 생산량 계산, 큐 등록/진행 기록/완료 처리, 현황/대기 조회.
- `view/production_view.py` (신규): 생산라인 콘솔 입출력.
- `controller/production_controller.py` (신규): 생산라인 메뉴 흐름 제어.
- `tests/test_order_model.py` (수정): `find_by_id`/`update_status` 테스트 추가.
- `tests/test_production_model.py` (신규)
- `tests/test_production_repository.py` (신규)
- `tests/test_production_controller.py` (신규)
- `reports/Report-step3.md` (신규, 본 문서)

### 작성한 테스트

- `tests/test_order_model.py` (기존 파일에 추가)
  - `find_by_id`가 존재하지 않는 주문번호에 `None`을 반환하는지 확인.
  - `update_status`가 상태를 변경하고 재조회 시 반영되는지 확인.
  - 존재하지 않는 주문번호로 `update_status` 호출 시 `OrderValidationError`를 발생시키는지 확인.

- `tests/test_production_model.py`
  - 등록되지 않은 시료 ID로 등록 시도 시 거부.
  - 부족분 0/음수/비정수 값으로 등록 시도 시 거부(파라미터라이즈).
  - 수율이 정확히 0.0인 시료로 등록 시도 시 거부.
  - 실 생산량/총 생산 시간 계산 정확성(부족분 10, 수율 0.9 → 실 생산량 13, 총 생산 시간 130.0).
  - 등록된 항목이 큐 맨 뒤(진행 중 항목)로 들어가고 누적 생산량이 0으로 시작하는지 확인.
  - 진행 중인 항목이 없을 때 진행 기록 시도 시 거부.
  - 여러 번 나누어 기록 시 누적 생산량이 정확히 합산되는지 확인.
  - 누적 생산량이 실 생산량에 도달 시 자동 완료 처리 및 주문 상태 CONFIRMED 전환 확인.
  - 실 생산량을 초과하는 수량 입력 시에도 캡핑되어 정상적으로 완료 처리되는지 확인.
  - 대상 주문이 PRODUCING이 아닐 때(RESERVED) 완료 처리 시도 시 중단·오류 발생, 주문 상태 미변경, 큐에서 제거되지 않음을 확인.
  - 완료 처리 후 다음 대기 항목이 새로운 진행 중 항목으로 승계되는지 확인.
  - 큐가 비어 있을 때 `current_job`/`waiting_jobs`가 각각 `None`/빈 리스트를 반환하는지 확인.
  - 여러 항목 등록 시 `waiting_jobs`가 FIFO(등록 순서)를 지키는지 확인.
  - 프로세스 재시작(새 `ProductionModel` 인스턴스) 후 생산 큐(등록 항목 + 누적 생산량)가 유지되는지 확인.

- `tests/test_production_repository.py`
  - 파일이 없을 때 `load_all`이 빈 리스트를 반환하는지 확인.
  - `save_all`이 레코드를 기록하고 임시 파일(`.tmp`)을 남기지 않는지 확인.
  - `save_all`을 반복 호출할 때 이전 내용을 덮어쓰는지 확인.

- `tests/test_production_controller.py`
  - 등록 메뉴 흐름: 성공 시 등록 완료 메시지, 미등록 시료 ID/비정수 부족분 입력 시 실패 메시지와 큐 미변경 확인.
  - 진행 기록 메뉴 흐름: 미완료 시 누적/실생산량 비율 메시지, 완료 시 CONFIRMED 전환 메시지와 실제 주문 상태 전환 확인, 진행 중 항목이 없을 때 실패 메시지 확인.
  - 생산 현황 조회 메뉴 흐름: 큐가 비었을 때 `None` 전달 확인.
  - 대기 주문 확인 메뉴 흐름: 큐가 비었을 때 빈 리스트, 진행 중 항목을 제외한 나머지가 FIFO로 전달되는지 확인.

### 검증

- `python -m py_compile`로 신규/수정 파일 문법 확인.
- 역할 지침(ai-action.md)은 테스트 실행 검증까지는 요구하지 않지만(그 역할은 test-verifier), 구현 단계에서의 명백한 오류를 조기에 걸러내기 위해 `pytest`를 직접 실행하여 confirm했다: 프로젝트 전체 80개 테스트(기존 Step 1/2 포함) 모두 통과.

### 재실행 사유

- 해당 없음(최초 구현).
