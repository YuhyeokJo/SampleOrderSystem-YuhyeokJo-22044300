# PRD-step9.md - 버그 수정 및 종합 시나리오 테스트 기능 명세

## 1. 버그 수정: `MonitoringModel` None fallback 누락

### 현재 동작 (결함)
```python
class MonitoringModel:
    def __init__(self, sample_model, order_model):
        self._sample_model = sample_model
        self._order_model = order_model
```
`MonitoringController.__init__`은 `MonitoringModel(sample_model, order_model)`을 호출하는데,
`sample_model`/`order_model` 인자의 기본값이 `None`이다. `MainController`의
`_default_controllers()`가 항상 `MonitoringController()`를 인자 없이 생성하므로, 실제 콘솔
실행에서는 항상 `MonitoringModel(None, None)`이 만들어지고, `count_orders_by_status()`/
`sample_stock_status()` 호출 시 `None.all()` 등에서 `AttributeError`가 발생해 프로그램이
종료된다.

### 수정 내용
`model/monitoring_model.py`의 생성자를 다른 모델(`SampleModel`, `OrderModel`,
`ProductionModel`, `ApprovalModel`, `ReleaseModel`)과 동일한 패턴으로 수정한다.

```python
def __init__(self, sample_model=None, order_model=None):
    self._sample_model = sample_model or SampleModel()
    self._order_model = order_model or OrderModel()
```
(`model.sample_model.SampleModel`, `model.order_model.OrderModel` import 추가)

### 회귀 테스트 (반드시 포함)
- `MonitoringModel()`을 인자 없이 생성해도 예외가 발생하지 않는지 확인(생성자 자체 검증).
- 데이터가 전혀 없는 상태(파일이 존재하지 않는 임시 디렉터리)에서 `MonitoringController()`를
  인자 없이 생성해 `run()`으로 "1. 주문량 확인"과 "2. 재고량 확인"을 각각 실행했을 때,
  예외 없이 기존에 정의된 빈 상태 안내(4개 상태 모두 0건, "등록된 시료가 없습니다.")가
  출력되는지 확인한다.
- 기존에 `sample_model`/`order_model`을 명시적으로 주입하던 테스트(`tests/test_monitoring_model.py`,
  `tests/test_monitoring_controller.py`)는 그대로 유지하고 통과해야 한다(주입 시 동작은
  변경하지 않음).

## 2. 버그 수정: 컨트롤러 간 `SampleModel`/`OrderModel` 인스턴스 미공유

### 현재 동작 (결함)
`controller/main_controller.py`의 `_default_controllers()`는 `SampleController()`,
`OrderController()`, `ApprovalController()`, `ProductionController()`,
`ReleaseController()`, `MonitoringController()`를 각각 인자 없이 개별 생성한다. 이 컨트롤러들이
사용하는 `OrderModel`, `ApprovalModel`, `ProductionModel`, `MonitoringModel`은 각각 필요한
`SampleModel`/`OrderModel`을 자기 자신의 생성자 안에서 새로 만든다(예:
`OrderModel.__init__`의 `self._sample_model = sample_model or SampleModel()`). 그 결과
`MainController()` 생성 시점에 서로 완전히 다른 `SampleModel`/`OrderModel` 인스턴스 여러
개가 만들어지고, 각 인스턴스는 생성 시점에 파일에서 한 번 읽은 내용을 메모리에 캐시한 채
그 이후로는 다시 읽지 않는다. 아래 최소 재현으로 확인된다.

```python
sm1 = SampleModel()
om = OrderModel()          # 내부적으로 자기만의 SampleModel()을 새로 만듦
sm1.register('S-001', 'Wafer', 1.0, 0.9, 100)
om.reserve('S-001', 'Cust', 10)
# -> OrderValidationError: 시료 ID 'S-001'는 등록되어 있지 않습니다.
```
즉 실제 콘솔에서 시료를 등록한 뒤 같은 세션에서 그 시료로 주문을 접수하는 정상적인 사용
흐름조차 지금은 실패한다. 이 결함이 있으면 아래 3절의 종합 시나리오 테스트가 3단계(시료
주문 접수)에서부터 실패한다.

### 수정 내용
`controller/main_controller.py`의 `_default_controllers()`를 아래와 같이 수정하여,
`SampleModel`, `OrderModel`, `ProductionModel`을 각각 한 번만 생성해 이를 필요로 하는 모든
하위 모델/컨트롤러에 동일한 인스턴스로 주입한다.

```python
def _default_controllers():
    sample_model = SampleModel()
    order_model = OrderModel(sample_model=sample_model)
    production_model = ProductionModel(sample_model=sample_model, order_model=order_model)
    approval_model = ApprovalModel(
        order_model=order_model, sample_model=sample_model, production_model=production_model
    )
    release_model = ReleaseModel(order_model=order_model)
    monitoring_model = MonitoringModel(sample_model, order_model)

    return {
        "1": SampleController(model=sample_model),
        "2": OrderController(model=order_model),
        "3": ApprovalController(model=approval_model),
        "4": MonitoringController(model=monitoring_model),
        "5": ProductionController(model=production_model),
        "6": ReleaseController(model=release_model),
    }
```
각 모델/컨트롤러 클래스 자체의 생성자 시그니처나 판단 로직은 변경하지 않는다(이미 외부
인스턴스를 주입받을 수 있는 파라미터를 갖추고 있었음). `MainController._show_summary()`가
매 루프마다 새 `SampleModel()`을 생성해 파일에서 다시 읽는 기존 방식(Step 7에서 확정, 공유
인스턴스의 최신 저장 내용을 디스크를 통해 읽어오므로 여전히 올바르게 동작함)은 그대로
유지하고 변경하지 않는다.

### 회귀 테스트 (반드시 포함)
- `tmp_path`로 격리한 뒤 `MainController()`를 인자 없이 생성한다. 시료 관리 메뉴(`1`)로
  시료 하나를 등록하고, 같은 `MainController` 세션 안에서 시료 주문 메뉴(`2`)로 그 시료를
  주문했을 때, "등록되어 있지 않습니다" 오류 없이 정상적으로 RESERVED 주문이 생성되는지
  확인한다.
- 기존에 각 모델에 `sample_model`/`order_model` 등을 명시적으로 주입하던 단위 테스트는
  그대로 유지하고 통과해야 한다.

## 3. 종합 시나리오 테스트: `tests/test_end_to_end_scenario.py`

이 시나리오 테스트는 위 1번(`MonitoringModel` fallback)과 2번(공유 인스턴스 배선) 수정이
모두 반영된 이후에만 끝까지 성립한다. 두 수정이 반영되지 않은 상태로는 3단계(시료 주문
접수)와 1단계(모니터링)에서 각각 실패하므로, 반드시 1번·2번 수정을 먼저 적용한 뒤 이
시나리오 테스트를 작성·실행한다.

### 목적
개별 기능 단위 테스트만으로는 발견하기 어려운, 여러 컨트롤러/모델이 실제 콘솔 진입 경로
(`MainController`의 기본 생성자 조합)를 통해 서로 연결되는 지점의 결함을 잡아낸다(이번에
발견한 모니터링 버그가 대표적 사례 — 단위 테스트는 항상 모델을 명시적으로 주입해 통과했지만
실제 콘솔 경로에서는 실패했다).

### 테스트 격리 방식
- `monkeypatch.chdir(tmp_path)`로 현재 작업 디렉터리를 임시 폴더로 전환한다. 이렇게 하면
  `SampleModel()`/`OrderModel()`/`ProductionModel()` 등이 기본 생성자로 사용하는
  상대경로 저장 파일(`samples.json`, `orders.json`, `data/production_jobs.json`)이 임시
  폴더 안에 생성되어, 실제 프로젝트 데이터나 다른 테스트에 영향을 주지 않는다.
- `MainController()`는 인자 없이 생성하여, `_default_controllers()`가 만드는 실제 콘솔
  경로(각 컨트롤러의 기본 생성자 조합)를 그대로 사용한다. 이는 이번 버그가 재현된 바로 그
  경로이므로, 이 경로를 통하지 않으면 이런 종류의 결함을 다시 놓칠 수 있다.
- `input()`을 `monkeypatch.setattr("builtins.input", ...)`으로 모의해, 미리 정해둔 입력
  목록을 순서대로 반환하도록 한다(콘솔에서 사용자가 실제로 타이핑하는 것을 시뮬레이션).
- `capsys`로 표준출력 전체를 캡처한다.
- 주문번호(`ORD-YYYYMMDD-XXXX`)가 실행 시점의 실제 날짜에 좌우되지 않도록,
  `unittest.mock.patch`로 `model.order_model.date`(또는 `date.today`)를 고정된 날짜(예:
  `date(2026, 7, 15)`)를 반환하도록 모의한다.

### 입력 스크립트 및 검증 항목 (순서대로)

1. **초기 상태 모니터링(빈 데이터, 버그 회귀 확인)**
   - 메인 메뉴에서 `4`(모니터링) → `1`(주문량 확인) → 결과 확인(회귀 테스트: 예외 없이
     4개 상태 모두 0건) → `2`(재고량 확인) → 결과 확인(예외 없이 "등록된 시료가 없습니다.")
     → `3`(모니터링 메뉴 종료, 메인 메뉴로 복귀).

2. **더미 시료 등록** (메인 메뉴 `1` → 시료 관리)
   - 시료 A: ID `S-001`, 이름 `실리콘 웨이퍼`, 평균 생산시간 `1`, 수율 `0.9`, 초기 재고
     `100` (충분한 재고 시나리오용).
   - 시료 B: ID `S-002`, 이름 `GaN 웨이퍼`, 평균 생산시간 `1`, 수율 `0.9`, 초기 재고 `5`
     (부족 재고 시나리오용).
   - 등록 후 `2`(시료 목록 조회)로 두 시료가 모두 표시되는지 확인, `4`(종료)로 메인 메뉴 복귀.

3. **시료 주문 접수** (메인 메뉴 `2` → 시료 주문)
   - 주문 1: 시료 `S-001`, 고객명 `테스트고객A`, 수량 `50`(재고 100 이내 → 승인 시 충분).
   - 주문 2: 시료 `S-002`, 고객명 `테스트고객B`, 수량 `20`(재고 5보다 많음 → 승인 시 부족,
     부족분 15).
   - 주문 3: 시료 `S-001`, 고객명 `테스트고객C`, 수량 `10`(거절 처리 대상).
   - 각 접수 성공 시 주문번호가 출력되는지 확인, `2`(종료)로 메인 메뉴 복귀.

4. **주문 승인/거절** (메인 메뉴 `3` → 주문 승인/거절)
   - `1`(접수된 주문 목록 조회)로 3건이 RESERVED로 표시되는지 확인.
   - 주문 1 승인(`2` → 주문번호 입력) → 재고 충분으로 즉시 CONFIRMED 전환 확인(부족분 없음).
   - 주문 2 승인(`2` → 주문번호 입력) → 재고 부족으로 PRODUCING 전환 및 부족분 15 안내 확인.
   - 주문 3 거절(`3` → 주문번호 입력) → REJECTED 전환 확인.
   - `4`(종료)로 메인 메뉴 복귀.

5. **생산라인** (메인 메뉴 `5` → 생산라인)
   - `3`(생산 현황 조회)로 주문 2에 대한 생산 항목이 현재 진행 중으로 표시되는지 확인(부족분
     15, 실 생산량은 `ceil(15 / (0.9*0.9))`으로 계산된 값이지만 정확한 값을 미리 계산할
     필요는 없다). 이 시나리오에서는 큐에 등록된 생산 항목이 이 1건뿐이므로 항상 큐의 맨
     앞(현재 진행 중, `current_job()`)이 되며, `4`(대기 주문 확인, `waiting_jobs()`는 진행
     중인 항목을 제외한 나머지만 보여줌)로는 조회되지 않는다.
   - `2`(생산 진행 기록) → 이번에 생산된 수량으로 `999999`(실 생산량을 초과하는 매우 큰 값)를
     입력 → 한 번의 입력만으로 즉시 생산 완료 처리되어 주문 2의 상태가 PRODUCING → CONFIRMED로
     전환되는지 확인(생산량을 여러 번 나누어 입력하는 반복 없이 1회로 종료 — 시나리오 소요
     시간을 최소화하기 위한 의도적 설계).
   - `4`(대기 주문 확인) 또는 `3`(생산 현황 조회)로 큐가 비었는지 확인.
   - `5`(종료)로 메인 메뉴 복귀.

6. **출고 처리** (메인 메뉴 `6` → 출고 처리)
   - `1`(CONFIRMED 목록 조회)로 주문 1, 주문 2가 모두 CONFIRMED로 표시되는지 확인.
   - 주문 1 출고(`2` → 주문번호 입력) → RELEASE 전환 확인.
   - 주문 2 출고(`2` → 주문번호 입력) → RELEASE 전환 확인.
   - `3`(종료)로 메인 메뉴 복귀.

7. **최종 모니터링(데이터 채워진 상태)** (메인 메뉴 `4` → 모니터링)
   - `1`(주문량 확인) → RESERVED 0건, CONFIRMED 0건, PRODUCING 0건, RELEASE 2건으로
     집계되는지 확인(REJECTED 1건은 집계에서 제외되어야 함).
   - `2`(재고량 확인) → 시료 `S-001`은 재고 50(100-50 승인 시 차감)으로 "여유"(RESERVED
     수요 없음), 시료 `S-002`는 재고 0(5 전량 차감)으로 "고갈"로 표시되는지 확인.
   - `3`(종료)로 메인 메뉴 복귀.

8. **프로그램 종료** — 메인 메뉴에서 `7` 입력, 종료 메시지 확인 후 `MainController.run()`이
   정상적으로 반환되는지 확인.

### 최종 검증
- 캡처된 표준출력 전체(`capsys.readouterr().out`)에 `"Traceback"` 문자열이 포함되지 않는지
  확인한다(처리되지 않은 예외가 발생하지 않았음을 보증하는 최종 안전장치).
- 시나리오 전체가 `pytest` 실행 시 수 초 이내(생산 진행을 여러 번 나누지 않고 1회로 완료하는
  설계 덕분에)에 끝나는지 확인한다(정확한 시간 상한을 못 박지는 않되, 반복 루프 없이 선형
  흐름으로 구성되어 있음을 코드로 확인 가능해야 한다).

## 범위 제외
- 이 문서는 기존 Step 1~8에서 정의된 기능 동작을 변경하지 않는다(1번 `MonitoringModel`
  생성자 fallback 추가와 2번 `_default_controllers()` 공유 인스턴스 배선 수정은 모두 결함
  수정이며, 각 모델/컨트롤러가 이미 갖추고 있던 인스턴스 주입 파라미터를 올바르게 활용하도록
  바로잡는 것일 뿐 새로운 판단 로직이나 저장 방식을 추가하지 않는다).
- 콘솔 한글 인코딩 문제 등 이번에 발견된 버그와 무관한 사항은 다루지 않는다.
