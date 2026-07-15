## Step 4 구현 리포트

### 구현 범위
- `SampleModel.decrease_stock(sample_id, amount)`: 시료 ID 존재 여부, 차감 수량이 0 이상의 정수인지, 차감 후 재고가 음수가 되지 않는지를 검증한 뒤 재고를 차감하고 재저장한다. 위반 시 `SampleValidationError`를 발생시킨다.
- `OrderModel.list_reserved()`: 저장된 주문 중 상태가 `RESERVED`인 주문만 반환한다. 없으면 빈 리스트를 반환한다.
- `ApprovalModel`(신규, `model/approval_model.py`): 승인/거절의 공통 사전 검증(`_require_reserved_order`)을 구현하고,
  - `approve(order_id)`: 재고가 주문 수량 이상이면 주문 수량만큼 차감 후 `CONFIRMED`로 전환. 재고가 부족하면 부족분을 `ProductionModel.register`로 먼저 등록 시도하고, 성공 시에만 남은 재고 전량을 차감하고 `PRODUCING`으로 전환. 등록이 실패(예: 수율 0.0)하면 예외가 그대로 전파되어 재고 차감/상태 변경이 전혀 일어나지 않는다(등록을 재고 차감보다 먼저 수행하여 자연스러운 롤백 보장).
  - `reject(order_id)`: 사전 검증 통과 후 `REJECTED`로 전환. 재고/생산라인에는 영향 없음.
  - `list_reserved()`: `OrderModel.list_reserved()`를 위임 호출.
- 접수된 주문 목록 조회: `ApprovalController`/`ApprovalView`에서 `ApprovalModel.list_reserved()`를 사용해 주문번호/시료ID/고객명/주문수량/상태를 표 형태로 출력. 없으면 안내 메시지 출력.
- model/view/controller 계층 분리는 Step 1~3과 동일한 패턴(`ProductionModel`/`ProductionController` 구조 참고)을 따랐다.

### 생성/수정 파일 목록
- `model/sample_model.py` (수정): `decrease_stock`, `_index_of` 추가.
- `model/order_model.py` (수정): `list_reserved` 추가(기존 `RESERVED_STATUS` 상수를 `model/order.py`에서 import하여 재사용).
- `model/approval_model.py` (신규): 승인/거절 처리 도메인 모델.
- `view/approval_view.py` (신규): 메뉴 출력, 주문번호 입력, 접수 주문 목록/결과 메시지 출력.
- `controller/approval_controller.py` (신규): 메뉴 흐름 제어, 승인/거절/목록 조회 액션 처리.
- `tests/test_sample_model.py` (수정): `decrease_stock` 테스트 추가.
- `tests/test_order_model.py` (수정): `list_reserved` 테스트 추가.
- `tests/test_approval_model.py` (신규)
- `tests/test_approval_controller.py` (신규)

### 작성한 테스트
- `tests/test_sample_model.py` 추가분: 정상 차감, 경계값(재고 전량 차감 시 0), 재고 초과 차감 거부, 미등록 시료 ID 거부, 잘못된 차감 수량(음수/실수/문자열) 거부.
- `tests/test_order_model.py` 추가분: RESERVED 주문 없을 때 빈 목록, RESERVED/CONFIRMED/PRODUCING/REJECTED가 섞여 있을 때 RESERVED만 포함되는지 확인.
- `tests/test_approval_model.py`:
  - 존재하지 않는 주문번호로 승인/거절 시도 거부.
  - 이미 CONFIRMED/PRODUCING/REJECTED 상태인 주문의 재승인/재거절 거부(파라미터화).
  - 재고 충분 시 승인 → CONFIRMED 전환 및 재고 차감 확인.
  - 재고와 주문 수량이 정확히 같은 경계값 → CONFIRMED 전환, 재고 0.
  - 재고가 주문 수량보다 1 적은 경우 → PRODUCING 전환, 부족분 1 생산라인 등록 확인.
  - 재고가 0인 시료 승인 → 부족분이 주문 수량 전체로 계산되어 생산라인에 등록되는지 확인.
  - 수율 0.0 시료에 대해 재고 부족으로 승인 시도 → 생산라인 등록 실패로 승인 전체 취소, 재고/상태 변경 없음 확인.
  - 거절 성공 시 재고에 영향 없음 확인.
  - 재고 부족으로 승인된 주문의 생산이 완료된 뒤에도 시료의 일반 재고 수량이 변하지 않는지 확인(Step 3 `record_progress`와 연동).
  - RESERVED 주문 없을 때 목록 조회 → 빈 결과.
  - 여러 상태가 섞여 있을 때 목록 조회에 RESERVED만 포함되는지 확인.
  - 프로세스 재시작(새 인스턴스) 후 승인으로 변경된 주문 상태와 차감된 재고 수량이 유지되는지 확인.
- `tests/test_approval_controller.py`:
  - 재고 충분/부족 각각의 승인 흐름이 CONFIRMED/PRODUCING 메시지와 상태 전환을 올바르게 보고하는지 확인.
  - 존재하지 않는 주문번호 승인/거절 시 실패 메시지 확인.
  - 생산라인 등록 실패(수율 0.0)로 인한 승인 실패 시 상태/재고가 그대로인지 확인.
  - 거절 흐름이 REJECTED 전환과 완료 메시지를 보고하는지 확인.
  - 접수된 주문 목록 조회 흐름이 RESERVED 주문이 없을 때 빈 목록을, 섞여 있을 때 RESERVED만 표시하는지 확인.

전체 테스트(`pytest tests/ -q`)를 직접 실행하여 115개 테스트가 모두 통과함을 확인했다(실행 검증은 test-verifier의 역할이나, 구현 확인을 위해 직접 수행함).
