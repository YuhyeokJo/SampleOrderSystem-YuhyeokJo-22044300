# Plan-step6.md - 모니터링 구현 계획

## 목표
담당자가 현재 시스템 상태를 한눈에 파악할 수 있도록, 상태별 주문 수와 시료별 재고 상태를
집계해 보여주는 모니터링 기능을 구현한다. 이번 step은 Step 1(시료)/Step 2~5(주문)의 기존
데이터를 조회·집계만 하는 읽기 전용(read-only) 기능이며, 새로운 저장소를 추가하지 않는다.

## "주문 대비 재고" 판단 기준에 대한 설계 결정

원본 요구사항은 재고 상태를 "여유(주문 대비 재고 충분)/부족(주문 대비 재고 수량 부족)/고갈
(재고 수량이 0)"으로만 정의하고, "주문 대비"가 구체적으로 어떤 주문을 가리키는지는 명시하지
않는다. 이번 step에서는 아래와 같이 해석을 확정한다.

- 시료의 재고는 Step 4(주문 승인)에서 승인 시점에 이미 소비(차감)되므로, `CONFIRMED`/
  `PRODUCING`/`REJECTED`/`RELEASE` 상태의 주문은 이미 재고에 반영이 끝난 상태다.
- 따라서 "주문 대비"의 "주문"은 **아직 처리되지 않아 향후 재고를 소비하게 될 `RESERVED`
  상태의 주문**을 의미하는 것으로 해석한다.
- 시료별 판단 순서:
  1. 재고 수량이 정확히 0이면 무조건 **고갈**.
  2. 그렇지 않으면, 해당 시료를 대상으로 하는 RESERVED 주문 수량의 합(수요)과 재고 수량을
     비교한다. 재고가 수요 이상이면 **여유**, 재고가 수요보다 적으면(재고 > 0인 상태에서)
     **부족**으로 표기한다. 해당 시료를 대상으로 하는 RESERVED 주문이 없으면 수요를 0으로
     보아 재고가 0보다 큰 이상 **여유**로 표기한다.

## 범위

- 주문량 확인: 상태별(RESERVED/CONFIRMED/PRODUCING/RELEASE) 주문 수를 집계해 표시한다.
  REJECTED 상태는 집계에서 제외한다.
- 재고량 확인: 등록된 각 시료의 현재 재고 수량과, 위 설계 결정에 따라 판정한 상태(여유/부족/
  고갈)를 함께 표시한다.

## 범위 제외

- 시료/주문/생산/승인·거절/출고 데이터를 변경하는 어떠한 기능도 이번 step에서 추가하지 않는다
  (모니터링은 조회 전용).
- 메인 메뉴 통합은 이번 step에서 다루지 않는다(Step 7에서 다룬다).

## 참고할 기존 프로젝트 구조 및 이전 step 산출물

- `ConsoleMVC-YuhyeokJo-22044300`: model/view/controller 계층 분리 패턴을 그대로 따른다.
- `DataMonitor-YuhyeokJo-22044300`: 콘솔에서 현재 상태를 표/패널 형태로 보여주는 구성 방식을
  참고한다(다만 이 프로젝트는 실시간 파일 감시 기반이고, 이번 step은 단순 조회 메뉴이므로
  실시간 감시(watchdog) 기능은 가져오지 않는다).
- Step 1 산출물(`model/sample_model.py`): 전체 시료 조회(`all()`)를 재사용해 재고량 확인에
  사용한다.
- Step 2~5 산출물(`model/order_model.py`): 전체 주문 조회(`all()`)와 `list_reserved()`를
  재사용해 주문량 확인/재고 상태 판단에 사용한다.

## 예상 산출물 구조 (예시)

```
model/
  monitoring_model.py       # MonitoringModel(상태별 주문 수 집계, 시료별 재고 상태 판정)
view/
  monitoring_view.py         # 모니터링 관련 콘솔 입출력
controller/
  monitoring_controller.py   # 모니터링 메뉴 흐름 제어
tests/
  test_monitoring_model.py
  test_monitoring_controller.py
```
※ 정확한 파일 구성은 `prds/PRD-step6.md` 검토 및 ai-action 구현 시 확정한다.

## 검증 체크리스트 (compliance-verifier 대조 기준)

- [ ] 상태별(RESERVED/CONFIRMED/PRODUCING/RELEASE) 주문 수 집계 기능 구현, REJECTED 제외
- [ ] 시료별 현재 재고 수량 표시 기능 구현
- [ ] 재고 상태(여유/부족/고갈) 판정 로직 구현(재고 0 → 고갈, 그 외 RESERVED 주문 수량 합과
      비교하여 여유/부족 판정)
- [ ] 새로운 저장소를 추가하지 않고 기존 Step 1/Step 2~5 데이터만 조회하여 집계
- [ ] 각 기능에 대응하는 단위 테스트 작성 및 통과
- [ ] REPORT.md(또는 `reports/Report-step6.md`) 작성

## 다음 절차

1. 이 Plan-step6.md 검토/승인 → 커밋
2. `prds/PRD-step6.md` 작성 → 검토/승인
3. agent 파이프라인 실행: `consistency-verifier` → `ai-action` → (`test-verifier` ∥ `compliance-verifier`)
4. 모든 agent PASS 후 구현 커밋 및 push
