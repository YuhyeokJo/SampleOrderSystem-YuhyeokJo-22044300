## Step 9 구현 리포트

### 구현 범위

- **버그 수정 (1) — `MonitoringModel` None fallback 누락** (PRD-step9.md 1절)
  - `model/monitoring_model.py`의 `__init__(self, sample_model=None, order_model=None)`이
    `sample_model`/`order_model`이 `None`일 때 각각 `SampleModel()`/`OrderModel()`로
    대체하도록 수정 완료(이전 ai-action 실행에서 이미 반영, 이번 실행에서 재확인만 수행).

- **버그 수정 (2) — 컨트롤러 간 `SampleModel`/`OrderModel`/`ProductionModel` 인스턴스
  미공유** (PRD-step9.md 2절)
  - `controller/main_controller.py`의 `_default_controllers()`를 PRD에 명시된 코드
    그대로 수정하여, `SampleModel`, `OrderModel(sample_model=...)`,
    `ProductionModel(sample_model=..., order_model=...)`을 각각 한 번만 생성하고
    `ApprovalModel`, `ReleaseModel`, `MonitoringModel`에도 동일 인스턴스를 주입하도록
    배선을 수정했다. 각 컨트롤러(`SampleController`, `OrderController`,
    `ApprovalController`, `MonitoringController`, `ProductionController`,
    `ReleaseController`)는 `model=` 파라미터로 이 공유 모델들을 전달받는다.
  - 각 모델/컨트롤러 클래스 자체의 생성자 시그니처나 판단 로직은 변경하지 않았다.
  - `MainController._show_summary()`는 기존 방식(매 루프 새 `SampleModel()`로 파일에서
    재조회)을 그대로 유지했다.

- **회귀 테스트 추가** (PRD-step9.md 1절·2절)
  - `tests/test_monitoring_model.py`, `tests/test_monitoring_controller.py`: 이전 실행에서
    이미 추가된 `MonitoringModel()`/`MonitoringController()` 무인자 생성 및 빈 데이터
    상태 회귀 테스트 확인, 그대로 유지.
  - `tests/test_main_controller.py`: `MainController()`를 인자 없이 생성한 단일 세션에서
    시료 관리 메뉴(`1`)로 시료를 등록한 뒤 같은 세션의 시료 주문 메뉴(`2`)로 그 시료를
    주문했을 때 "등록되어 있지 않습니다" 오류 없이 "예약 접수 완료."가 출력되는지 확인하는
    `test_default_controllers_share_sample_model_across_menus`를 추가했다.

- **종합 시나리오 테스트 추가** (PRD-step9.md 3절)
  - `tests/test_end_to_end_scenario.py`를 신규 작성하여, `MainController()`를 인자 없이
    구동해 PRD 3절의 8단계 시나리오(초기 모니터링 → 시료 2종 등록 → 주문 3건 접수 →
    승인 2건/거절 1건 → 생산(999999 1회 입력으로 즉시 완료) → 출고 2건 → 최종 모니터링 →
    프로그램 종료)를 정확한 입력값과 순서로 재현했다.
  - `monkeypatch.chdir(tmp_path)`로 파일 저장 경로를 격리하고, `unittest.mock.patch`로
    `model.order_model.date`를 `date(2026, 7, 15)`로 고정해 주문번호를 결정적으로 만들었다.
  - `capsys`로 캡처한 전체 출력에 `"Traceback"`이 없는지, 각 단계별 기대 문구(등록/주문/
    승인/거절/생산완료/출고/최종 집계)가 정확히 출력되는지 검증한다.

### 생성/수정 파일 목록

- `controller/main_controller.py` (수정) — `_default_controllers()`가 `SampleModel`,
  `OrderModel`, `ProductionModel`, `ApprovalModel`, `ReleaseModel`, `MonitoringModel`을
  공유 인스턴스로 배선하도록 수정.
- `model/monitoring_model.py` (이전 실행에서 수정, 이번에 재확인) — 생성자 fallback 패턴
  적용 상태 유지.
- `tests/test_main_controller.py` (수정) — 컨트롤러 간 모델 공유 회귀 테스트 추가.
- `tests/test_monitoring_model.py`, `tests/test_monitoring_controller.py` (이전 실행에서
  수정, 이번에 재확인) — `MonitoringModel`/`MonitoringController` 무인자 생성 회귀 테스트
  유지.
- `tests/test_end_to_end_scenario.py` (신규) — 종합 시나리오 테스트.

### 작성한 테스트

- `tests/test_main_controller.py::test_default_controllers_share_sample_model_across_menus`
  — `MainController()`를 인자 없이 생성한 단일 세션에서 시료 등록(메뉴 1) 후 같은 시료로
  주문 접수(메뉴 2)가 "등록되어 있지 않습니다" 오류 없이 성공하는지 검증(버그 수정 2 회귀).
- `tests/test_end_to_end_scenario.py::test_full_console_scenario_runs_end_to_end_without_traceback`
  — 다음을 한 번의 콘솔 흐름으로 검증:
  - 데이터 없는 상태의 모니터링 진입 시 예외 없이 4개 상태 0건과 "등록된 시료가 없습니다."
    출력(버그 수정 1 회귀).
  - 시료 S-001(재고 100)/S-002(재고 5) 등록 및 목록 조회.
  - 주문 3건 접수(S-001 수량 50, S-002 수량 20, S-001 수량 10) 및 각 주문번호 출력 확인.
  - 주문 1 승인(재고 충분, 부족분 없음), 주문 2 승인(재고 부족, 부족분 15 및 생산라인 등록
    안내), 주문 3 거절(REJECTED) 확인.
  - 생산 현황 조회로 진행 중 항목 확인 후 `999999` 1회 입력으로 즉시 생산 완료
    (PRODUCING → CONFIRMED) 및 대기 큐 빈 상태 확인.
  - 출고 처리 2건(RELEASE 전환) 확인.
  - 최종 모니터링에서 RELEASE 2건 집계(REJECTED 제외) 및 재고 상태([고갈] 포함) 확인.
  - 프로그램 종료 메시지 확인.
  - 전체 캡처 출력에 `"Traceback"` 문자열이 없음을 최종 확인.

### 검증 결과

- `python -m pytest -q` 전체 실행 결과 196개 테스트 모두 통과(회귀 없음).
- 종합 시나리오 테스트는 생산 진행 기록을 1회 큰 값 입력으로 즉시 완료시키는 설계 덕분에
  0.33초 내 완료됨.

### 재실행 사유

이번 실행은 최초 재실행이 아니라, 직전 실행에서 버그 수정 (1)과 관련 회귀 테스트까지 완료한
뒤 발견한 버그 수정 (2)(컨트롤러 간 모델 인스턴스 미공유)를 Plan-step9.md/PRD-step9.md에
반영한 후 이어서 진행한 작업이다. 버그 수정 (1) 관련 코드와 테스트는 재확인만 하고 그대로
유지했으며, 이번에는 `controller/main_controller.py`의 `_default_controllers()` 수정,
관련 회귀 테스트, 종합 시나리오 테스트를 추가로 완료했다.
