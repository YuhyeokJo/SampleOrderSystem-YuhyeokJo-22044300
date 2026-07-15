# Plan-step9.md - 버그 수정 및 종합 시나리오 테스트 추가 구현 계획

## 배경
콘솔에서 실제로 데이터가 없는 상태로 메인 메뉴 `[4] 모니터링`에 진입하면 아래와 같이
`AttributeError`가 발생하며 프로그램이 죽는 버그를 발견했다.

```
File "controller/monitoring_controller.py", line 30, in _show_order_counts
    counts = self.model.count_orders_by_status()
File "model/monitoring_model.py", line 22, in count_orders_by_status
    for order in self._order_model.all():
AttributeError: 'NoneType' object has no attribute 'all'
```

**원인**: `MonitoringController(model=None, view=None, sample_model=None, order_model=None)`은
`MonitoringModel(sample_model, order_model)`을 그대로 호출하는데, `MonitoringModel.__init__`은
다른 모든 모델(`SampleModel`, `OrderModel`, `ProductionModel` 등)과 달리 `sample_model`/
`order_model`이 `None`일 때 기본 인스턴스로 대체하는 fallback이 없다. `MainController`의
`_default_controllers()`는 항상 `MonitoringController()`를 인자 없이 생성하므로, 데이터
유무와 무관하게 메인 메뉴에서 모니터링에 진입하는 모든 경우에 이 버그가 재현된다. 이 버그는
기존 단위 테스트에서 잡히지 않았는데, 기존 `test_monitoring_model.py`가 항상
`MonitoringModel(sample_model, order_model)`에 실제 모델을 명시적으로 주입해서만 테스트했고,
`MainController`를 통한 실제 콘솔 진입 경로(인자 없는 기본 생성)를 검증하는 테스트가 없었기
때문이다.

## 배경 2: 컨트롤러 간 모델 인스턴스 미공유 버그 (종합 시나리오 테스트 작성 중 발견)

1번 버그를 수정한 뒤 종합 시나리오 테스트를 실제로 작성·구동하는 과정에서, 훨씬 더 심각한
버그를 추가로 발견했다: `MainController._default_controllers()`가
`SampleController()`, `OrderController()`, `ApprovalController()`, `ProductionController()`,
`ReleaseController()`, `MonitoringController()`를 각각 **인자 없이 개별 생성**하는데,
`OrderModel`/`ApprovalModel`/`ProductionModel`/`MonitoringModel`은 각각 자기 자신만의
독립적인 `SampleModel()`/`OrderModel()` 인스턴스를 내부에서 새로 만든다. 이 인스턴스들은
모두 `MainController()` 생성 시점(메인 메뉴가 처음 표시되기 전, 아직 아무 데이터도 없을 수
있는 시점)에 한 번만 각자 파일에서 데이터를 읽어 메모리에 캐시하고, 이후 다시 읽지 않는다.
그 결과, 시료 관리 메뉴에서 새 시료를 등록해도 그 등록 내용이 시료 주문/승인/생산/출고/
모니터링 메뉴가 내부적으로 사용하는 (완전히 별개의) `SampleModel`/`OrderModel` 인스턴스에는
전혀 반영되지 않는다. 최소 재현 스크립트로 다음을 직접 확인했다:

```python
sm1 = SampleModel()
om = OrderModel()          # 내부적으로 자기만의 SampleModel()을 새로 만듦
sm1.register('S-001', 'Wafer', 1.0, 0.9, 100)
om.reserve('S-001', 'Cust', 10)
# -> OrderValidationError: 시료 ID 'S-001'는 등록되어 있지 않습니다.
```

이는 실제 `python main.py`로 시료를 등록한 뒤 같은 세션에서 그 시료로 주문을 넣는, 지극히
정상적인 사용 흐름에서도 그대로 발생하는 실제 운영 결함이며, 이번에 추가하려는 종합
시나리오 테스트가 정확히 이 지점에서 실패한다. 사용자 확인 결과, 이 수정을 Step 9에
포함하여 함께 처리하기로 했다.

### 수정 방향
`controller/main_controller.py`의 `_default_controllers()`가 `SampleModel`, `OrderModel`,
`ProductionModel`을 각각 **한 번만 생성**하여 이를 필요로 하는 모든 하위 모델/컨트롤러에
동일한 인스턴스로 주입한다.

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
각 모델 클래스(`OrderModel`, `ApprovalModel`, `ProductionModel`, `ReleaseModel`,
`MonitoringModel`) 자체와 각 컨트롤러(`SampleController`, `OrderController` 등)는 이미 외부
인스턴스를 주입받을 수 있는 생성자 파라미터를 가지고 있으므로, 이 파라미터들의 동작 자체는
변경하지 않고 `MainController`의 배선(생성 및 전달) 방식만 수정한다. `MainController._show_summary()`가
매 루프마다 새 `SampleModel()`을 만들어 파일에서 다시 읽는 기존 방식(Step 7에서 확정, 디스크
매개 동기화로 이미 정상 동작 확인됨)은 그대로 유지하며 변경하지 않는다.

## 목표
1. `MonitoringModel`의 생성자 버그를 수정한다(다른 모델과 동일한 fallback 패턴 적용).
2. `MainController`가 하위 컨트롤러/모델 간 `SampleModel`/`OrderModel`/`ProductionModel`
   인스턴스를 공유하도록 배선을 수정하여, 한 메뉴에서의 데이터 변경이 같은 세션의 다른
   메뉴에도 즉시 반영되도록 한다.
3. 이 두 버그가 재발하지 않도록 회귀 테스트를 추가한다.
4. 실제 콘솔 흐름 전체(더미 시료 등록 → 주문 → 승인/거절 → 생산 → 출고 → 모니터링)를
   `MainController`를 통해 끝에서 끝까지 구동하는 종합 시나리오 테스트를 추가하여, 이번과
   같이 개별 단위 테스트만으로는 발견하기 어려운 통합 지점의 결함을 잡아낼 수 있도록 한다.

## 범위

### 1. 버그 수정 (1) — `MonitoringModel` fallback 누락
- `model/monitoring_model.py`의 `__init__`에서 `sample_model`/`order_model`이 `None`이면
  각각 `SampleModel()`/`OrderModel()`로 대체한다(다른 모델의 기존 패턴과 동일).
- 회귀 테스트: `MonitoringModel()`을 인자 없이 생성해도 예외가 발생하지 않고, 빈 데이터
  상태에서 `count_orders_by_status()`/`sample_stock_status()`가 정상적으로 빈 결과를
  반환하는지 확인한다. `MonitoringController()`를 인자 없이 생성해 `run()`으로 메뉴
  1번/2번을 실행했을 때도 예외 없이 안내 문구가 출력되는지 확인한다.

### 2. 버그 수정 (2) — 컨트롤러 간 모델 인스턴스 미공유
- `controller/main_controller.py`의 `_default_controllers()`를 위 "수정 방향"에 제시한
  대로 수정하여, `SampleModel`/`OrderModel`/`ProductionModel`을 한 번씩만 생성해 이를
  필요로 하는 모든 하위 모델/컨트롤러에 동일한 인스턴스로 주입한다.
- 회귀 테스트: `MainController()`를 인자 없이 생성한 뒤, 시료 관리 메뉴로 시료를 등록하고
  같은 `MainController` 세션 안에서 시료 주문 메뉴로 그 시료를 주문할 수 있는지(등록되지
  않았다는 오류가 발생하지 않는지) 확인한다.

### 3. 종합 시나리오 테스트 추가
- 새 테스트 파일(`tests/test_end_to_end_scenario.py`)에서 `MainController`를 실제로
  구동하여(입력을 스크립트로 미리 정해두고 `input`을 모의(mock)하는 방식) 아래 흐름을
  검증한다. 저장 파일 경로는 `tmp_path`로 격리해 다른 테스트나 실제 데이터에 영향을 주지
  않는다.
  1. **데이터가 없는 초기 상태에서 모니터링 진입** — 이번에 고친 버그의 회귀 확인(주문량
     확인/재고량 확인 모두 예외 없이 빈 상태 안내가 출력되는지).
  2. **더미 시료 등록**(시료 관리 메뉴) — 수율/재고 수량이 서로 다른 여러 시료를 등록한다
     (재고 충분 시나리오용 시료 1개, 재고 부족 시나리오용 시료 1개 이상).
  3. **시료 주문 접수**(시료 주문 메뉴) — 재고가 충분한 시료에 대한 주문과, 재고보다 많은
     수량을 주문하는(부족 유발) 주문을 각각 접수한다.
  4. **주문 승인/거절**(주문 승인/거절 메뉴) — 재고 충분 주문은 즉시 승인(CONFIRMED),
     재고 부족 주문은 승인(PRODUCING 전환 + 생산라인 등록)하고, 별도 주문 하나는 거절
     (REJECTED)한다.
  5. **생산라인**(생산라인 메뉴) — 생산 진행 기록 시 실제 필요한 정확한 실 생산량을 계산하지
     않고, 매우 큰 생산 수량 값을 한 번만 입력해 즉시 생산 완료(PRODUCING → CONFIRMED)
     처리되도록 한다(아래 "생산 시간 관련 설계 결정" 참고).
  6. **출고 처리**(출고 처리 메뉴) — CONFIRMED 상태가 된 주문들을 출고 처리(RELEASE)한다.
  7. **모니터링**(모니터링 메뉴) — 데이터가 채워진 상태에서 주문량 확인(RESERVED/CONFIRMED/
     PRODUCING/RELEASE 건수, REJECTED 제외 확인)과 재고량 확인(여유/부족/고갈 상태 확인)을
     실행해 예외 없이 올바른 값이 출력되는지 확인한다.
  8. 프로그램 종료.
  - 시나리오 전체에서 콘솔에 `Traceback`이나 처리되지 않은 예외 문구가 출력되지 않는지
    (capsys로 캡처한 출력 전체를 검사)를 최종적으로 확인한다.

### 생산 시간 관련 설계 결정 (mock 활용)
- 실 생산량/총 생산 시간은 시스템상 실제 대기 시간(예: `time.sleep`)을 소비하지 않는 순수
  수치 데이터이므로, 테스트가 실제로 오래 걸리는 원인은 "생산 진행 기록"을 실 생산량만큼
  여러 번 나누어 입력해야 한다는 점뿐이다. 시나리오 테스트에서는 생산 진행 기록 시 실제
  계산된 실 생산량을 미리 알 필요 없이 충분히 큰 값(예: `999999`)을 한 번만 입력하여, 생산
  모델이 이를 실 생산량으로 자동 캡핑해 즉시 완료 처리하는 기존 동작(PRD-step3.md 예외
  케이스: "한 번에 실 생산량을 초과하는 수량을 입력해도 누적 생산량이 실 생산량을 넘지 않고
  완료 처리")을 그대로 활용한다. 이를 통해 여러 차례 나누어 입력하는 긴 반복 없이 한 번의
  입력으로 생산을 완료시켜 테스트 소요 시간을 최소화한다.
- 주문번호(`ORD-YYYYMMDD-XXXX`)는 접수 시점의 실제 날짜에 의존하므로, 시나리오 테스트에서는
  `unittest.mock`으로 `model.order_model.date`(또는 `OrderModel`에 이미 있는
  `date_provider` 주입 지점)를 모의해 고정된 날짜를 사용하게 함으로써, 테스트 결과가 실행
  시점(오늘 날짜)에 따라 달라지지 않고 항상 동일하게 재현되도록 한다.

## 참고
- `MainController`는 하위 컨트롤러를 기본 생성자(인자 없음)로 생성하므로, 시나리오 테스트는
  저장 파일 경로가 실행 위치(cwd)에 대한 상대 경로로 정해지는 각 Repository의 기본 동작을
  그대로 이용한다. 테스트에서는 `monkeypatch.chdir(tmp_path)`로 현재 작업 디렉터리를 임시
  폴더로 바꿔 실제 프로젝트의 `data/*.json`, `samples.json`, `orders.json` 파일에 영향을
  주지 않도록 격리한다.

## 범위 제외
- 이번 step에서 새로운 기능(도메인 로직)을 추가하지 않는다. `MonitoringModel` 생성자
  fallback 추가와 `_default_controllers()`의 공유 인스턴스 배선 수정은 모두 버그 수정이며,
  각 모델/컨트롤러가 이미 갖추고 있던 외부 인스턴스 주입 파라미터를 `MainController`가
  실제로 활용하도록 배선을 바로잡는 것일 뿐, 어떤 모델의 판단 로직이나 저장 방식도 새로
  추가하거나 변경하지 않는다.
- 콘솔 인코딩(한글 깨짐) 등 이번에 발견된 버그와 무관한 별도 이슈는 이번 step에서 다루지
  않는다.

## 검증 체크리스트 (compliance-verifier 대조 기준)

- [ ] `MonitoringModel.__init__`이 `sample_model`/`order_model`이 `None`일 때 각각
      `SampleModel()`/`OrderModel()`로 대체함
- [ ] `MonitoringModel()`/`MonitoringController()`를 인자 없이 생성해도 예외가 발생하지
      않는 회귀 테스트 존재 및 통과
- [ ] `controller/main_controller.py`의 `_default_controllers()`가 `SampleModel`/
      `OrderModel`/`ProductionModel`을 한 번만 생성해 모든 하위 컨트롤러/모델에 동일한
      인스턴스로 주입함
- [ ] `MainController()`를 인자 없이 생성한 단일 세션 안에서 시료 등록 후 그 시료로 주문
      접수가 가능한지(등록되지 않았다는 오류가 발생하지 않는지) 확인하는 회귀 테스트 존재
      및 통과
- [ ] `tests/test_end_to_end_scenario.py`가 더미 시료 등록 → 주문 접수(충분/부족 각 1건
      이상) → 승인(충분/부족)·거절 → 생산 완료 → 출고 → 모니터링(데이터 있음/없음 각각)까지
      `MainController`를 통해 전체 콘솔 흐름으로 구동됨
- [ ] 생산 진행 기록을 큰 값 1회 입력으로 즉시 완료시켜 시나리오가 여러 차례 반복 없이
      빠르게 끝남
- [ ] 주문번호 생성에 사용되는 날짜가 `unittest.mock`(또는 `date_provider`)으로 고정되어
      테스트 결과가 실행 시점과 무관하게 결정적임
- [ ] 시나리오 실행 중 캡처한 콘솔 출력에 `Traceback`이나 처리되지 않은 예외 문구가 없음을
      확인
- [ ] 기존 단위 테스트가 모두 그대로 통과함(회귀 없음)
- [ ] REPORT.md(또는 `reports/Report-step9.md`) 작성

## 다음 절차

1. 이 Plan-step9.md 검토/승인 → 커밋
2. `prds/PRD-step9.md` 작성(정확한 입력 스크립트/검증 항목 명세) → 검토/승인
3. agent 파이프라인 실행: `consistency-verifier` → `ai-action` → (`test-verifier` ∥ `compliance-verifier`)
4. 모든 agent PASS 후 구현 커밋 및 push
