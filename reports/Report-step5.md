## Step 5 구현 리포트

### 구현 범위
- `OrderModel`에 `list_confirmed()`를 추가하여 상태가 `CONFIRMED`인 주문만 반환하도록 구현했다. 기존 `list_reserved()`와 동일한 패턴을 따랐으며, CONFIRMED 주문이 없으면 빈 리스트를 반환한다.
- `ReleaseModel`(신규)을 구현했다.
  - `list_confirmed()`: `OrderModel.list_confirmed()`를 그대로 위임 호출한다.
  - `release(order_id)`: 주문번호로 조회 후 존재하지 않으면 `OrderValidationError`를 발생시키고, 상태가 `CONFIRMED`가 아니면(RESERVED/PRODUCING/REJECTED/이미 RELEASE 포함) 오류로 거부한다. CONFIRMED인 경우에만 `OrderModel.update_status(order_id, "RELEASE")`를 호출해 상태를 전환하며, `SampleModel`/`ProductionModel`은 전혀 호출하지 않아 재고·생산라인에 영향을 주지 않는다.
- CONFIRMED 주문 목록 조회 콘솔 기능(`ReleaseView.show_confirmed_orders`, `ReleaseController._show_confirmed_orders`)을 구현했다. 주문번호/시료ID/고객명/주문수량/상태를 표 형태로 출력하며, 목록이 없으면 안내 메시지를 출력한다.
- 출고 처리 콘솔 기능(`ReleaseController._release_order`)을 구현했다. 성공 시 전환된 주문번호와 RELEASE 상태를 안내하고, 실패 시 사유를 안내한다.
- Step 1~4와 동일하게 model(데이터/검증)·view(콘솔 입출력)·controller(흐름 제어) 계층을 분리했으며, Step4의 `approval_model.py`/`approval_view.py`/`approval_controller.py` 구조를 그대로 참고했다.
- 재고, 생산라인, 승인/거절 로직은 수정하지 않고 기존 `OrderModel.find_by_id`/`update_status`만 재사용했다. 모니터링, 메인 메뉴 통합은 범위에서 제외했다.

### 생성/수정 파일 목록
- `model/order_model.py` (수정): `CONFIRMED_STATUS` 상수와 `list_confirmed()` 메서드 추가.
- `model/release_model.py` (신규): 출고 처리 도메인 모델 `ReleaseModel`.
- `view/release_view.py` (신규): 출고 처리 메뉴/목록 출력 등 콘솔 입출력.
- `controller/release_controller.py` (신규): 출고 처리 메뉴 흐름 제어.
- `tests/test_order_model.py` (수정): `list_confirmed()` 테스트 추가.
- `tests/test_release_model.py` (신규): `ReleaseModel` 단위 테스트.
- `tests/test_release_controller.py` (신규): `ReleaseController` 단위 테스트.

### 작성한 테스트
- `tests/test_order_model.py`
  - `test_list_confirmed_when_no_orders_returns_empty`: CONFIRMED 주문이 없을 때 빈 리스트 반환 확인.
  - `test_list_confirmed_includes_only_confirmed_status_orders`: RESERVED/CONFIRMED/PRODUCING/REJECTED/RELEASE가 섞여 있을 때 CONFIRMED만 포함되는지 확인.
- `tests/test_release_model.py`
  - `test_release_rejects_unknown_order_id`: 존재하지 않는 주문번호로 출고 시도 시 거부.
  - `test_release_rejects_order_not_in_confirmed_status` (parametrize: RESERVED/PRODUCING/REJECTED/RELEASE): 각 비-CONFIRMED 상태에서 출고 시도 시 거부.
  - `test_release_transitions_confirmed_order_to_release_status`: CONFIRMED 주문 출고 시 RELEASE로 전환 성공.
  - `test_release_does_not_affect_sample_stock`: 출고 처리 후 시료 재고 수량이 변하지 않는지 확인.
  - `test_list_confirmed_when_no_orders_returns_empty` / `test_list_confirmed_includes_only_confirmed_status_orders`: `ReleaseModel.list_confirmed()`가 `OrderModel.list_confirmed()`와 동일하게 동작하는지 확인.
  - `test_release_state_persists_after_restart_with_new_instances`: 프로세스 재시작(새 인스턴스) 후 RELEASE 상태가 유지되는지 확인.
- `tests/test_release_controller.py`
  - `test_release_flow_transitions_confirmed_order_to_release`: 메뉴 흐름을 통한 출고 성공 및 완료 메시지 확인.
  - `test_release_flow_reports_failure_for_unknown_order_id`: 존재하지 않는 주문번호에 대한 실패 메시지 확인.
  - `test_release_flow_reports_failure_when_order_not_confirmed`: RESERVED 상태 주문에 대한 출고 거부 및 상태 유지 확인.
  - `test_show_confirmed_orders_flow_when_no_orders_reports_empty`: CONFIRMED 주문이 없을 때 빈 목록 안내 확인.
  - `test_show_confirmed_orders_flow_includes_only_confirmed_orders`: 목록 조회 시 CONFIRMED 주문만 표시되는지 확인.

pytest 전체 실행 결과 132개 테스트 모두 통과했다(최종 검증은 test-verifier 역할).
