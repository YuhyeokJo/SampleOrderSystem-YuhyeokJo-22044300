# Plan-step3.md - 생산라인 구현 계획

## 목표
재고 부족분에 대한 실 생산량/생산 시간을 계산하고, FIFO 생산 큐를 관리하며, 생산 진행 상황을
기록하고 완료 시 주문 상태를 전환하는 생산라인 기능을 구현한다. Plan.md에 따라, 다음 step인
주문 승인/거절(Step 4)이 재고 부족 시 이 생산라인 기능을 호출하므로 이번 step에서 먼저
공개 인터페이스(생산 항목 등록/조회/진행 기록)를 확정한다.

## Step 4 선행 배치에 따른 설계 결정

Step 4(주문 승인/거절)가 아직 존재하지 않는 상태에서 생산라인을 먼저 구현하므로, 아래와 같이
경계를 정한다.

- 이번 step은 "생산 항목을 생산 큐에 등록하는 것"부터 시작한다. 실제 운영에서는 Step 4의
  주문 승인 로직이 재고 부족을 판단해 이 등록 기능을 호출하지만, 이번 step 자체의 테스트에서는
  등록 함수를 직접 호출하는 방식으로 검증한다.
- 생산 완료 처리(PRODUCING → CONFIRMED)를 위해서는 주문 상태를 갱신하는 기능이 필요하다.
  Step 2의 `Order`/`OrderModel`은 현재 접수(RESERVED) 생성만 지원하므로, 이번 step에서
  주문 상태를 변경하는 범용 기능(예: 상태 갱신 후 재저장)을 `OrderModel`에 추가한다. 이 기능은
  Step 4에서 승인/거절 시 상태 전환(RESERVED → CONFIRMED/PRODUCING/REJECTED)에도 재사용될
  것이다.
- 생산 항목을 큐에 등록하는 시점에는 대상 주문이 이미 `PRODUCING` 상태로 설정되어 있다고
  가정한다(Step 4가 담당). 이번 step의 테스트에서는 `OrderModel.reserve()`로 주문을 만든 뒤
  위에서 추가하는 상태 갱신 기능으로 `PRODUCING` 상태를 미리 만들어 두고 검증한다.

## 범위

- 생산량 계산: 실 생산량 = `ceil(부족분 / (수율 × 0.9))`, 총 생산 시간 = `평균 생산시간 × 실 생산량`.
  수율이 정확히 0.0인 시료(Step 1에서 등록 가능한 경계값)는 이 계산식이 0으로 나누는 연산이
  되므로, 생산 큐 등록 자체를 거부한다.
- FIFO 생산 큐: 생산 항목(주문 ID, 시료 ID, 부족분, 실 생산량, 총 생산 시간)을 큐에 등록하고
  선입선출 순서로 처리한다. 하나의 생산 라인은 시료를 하나씩만 생산하므로, 동시에 진행 중인
  생산 항목은 최대 1건이다.
- 생산 진행 기록 및 완료 처리: 현재 진행 중인 생산 항목에 대해 생산된 수량을 기록하고, 누적
  생산량이 실 생산량에 도달하면 생산이 완료된 것으로 보아 대상 주문이 실제로 `PRODUCING`
  상태인지 확인한 뒤 `CONFIRMED`로 전환하고, 큐의 다음 항목을 진행 상태로 넘긴다. 주문이
  `PRODUCING` 상태가 아니면 완료 처리를 중단하고 오류를 안내한다.
- 생산 현황 조회: 현재 진행 중인 생산 항목의 주문 정보와 지금까지의 누적 생산량을 표시한다.
  진행 중인 항목이 없으면 없음을 안내한다.
- 대기 주문 확인: 생산 큐에서 대기 중인(아직 진행 중이 아닌) 생산 항목 목록을 FIFO 순서대로
  출력한다.

## 범위 제외 (다음 step 이후)

- 주문 승인/거절 로직 자체(재고 판단, RESERVED → CONFIRMED/PRODUCING/REJECTED 최초 전환)는
  Step 4에서 다룬다. 이번 step은 생산 큐 등록/처리 기능만 제공한다.
- 출고 처리, 모니터링, 메인 메뉴 통합은 이번 step에서 다루지 않는다.
- 여러 개의 생산 라인(설비)을 두어 병렬로 생산하는 기능은 다루지 않는다(요구사항 6절: 하나의
  생산 라인은 시료를 하나씩 생산).

## 참고할 기존 프로젝트 구조 및 이전 step 산출물

- `ConsoleMVC-YuhyeokJo-22044300`: model/view/controller 계층 분리 패턴을 그대로 따른다.
- `DataPersistence-YuhyeokJo-22044300`: JSON 파일 기반 영속성(임시 파일 작성 후 `os.replace`
  원자적 교체) 방식을 생산 큐 데이터 저장에도 동일하게 적용한다.
- Step 1 산출물(`model/sample_model.py`)의 시료 조회 기능을 재사용하여 수율/평균 생산시간을
  가져온다.
- Step 2 산출물(`model/order_model.py`)에 주문 상태 갱신 기능을 추가하고, 이를 생산 완료 처리
  시 재사용한다.

## 예상 산출물 구조 (예시)

```
model/
  production_job.py       # 생산 항목 엔티티(주문 ID, 시료 ID, 부족분, 실 생산량, 총 생산 시간, 누적 생산량)
  production_repository.py # 생산 큐 JSON 영속성 (원자적 저장)
  production_model.py     # ProductionModel(생산량 계산, 큐 등록/진행 기록/완료 처리, 현황/대기 조회)
view/
  production_view.py       # 생산라인 관련 콘솔 입출력
controller/
  production_controller.py # 생산라인 메뉴 흐름 제어
tests/
  test_production_model.py
  test_production_repository.py
  test_production_controller.py
```
※ 정확한 파일 구성은 `prds/PRD-step3.md` 검토 및 ai-action 구현 시 확정한다.

## 검증 체크리스트 (compliance-verifier 대조 기준)

- [ ] 실 생산량 계산(`ceil(부족분 / (수율 × 0.9))`) 구현, 수율 0.0인 시료는 등록 거부
- [ ] 총 생산 시간 계산(`평균 생산시간 × 실 생산량`) 구현
- [ ] 생산 큐에 항목을 FIFO 순서로 등록/조회하는 기능 구현
- [ ] 생산 진행 기록 기능 구현(누적 생산량 갱신)
- [ ] 생산 완료 처리 구현(누적 생산량이 실 생산량 도달 시 대상 주문이 PRODUCING 상태인지 확인
      후 CONFIRMED로 전환, 다음 대기 항목으로 진행 전환; PRODUCING이 아니면 중단하고 오류 안내)
- [ ] 생산 현황 조회 기능 구현(현재 진행 중인 항목의 주문 정보 + 누적 생산량, 없으면 안내)
- [ ] 대기 주문 확인 기능 구현(FIFO 순서의 대기 목록)
- [ ] `OrderModel`에 주문 상태 갱신 기능 추가(Step 4 재사용 대비)
- [ ] JSON 파일 기반 영속성 적용(재시작 후에도 생산 큐 데이터 유지)
- [ ] 각 기능에 대응하는 단위 테스트 작성 및 통과
- [ ] REPORT.md(또는 `reports/Report-step3.md`) 작성

## 다음 절차

1. 이 Plan-step3.md 검토/승인 → 커밋
2. `prds/PRD-step3.md` 작성 → 검토/승인
3. agent 파이프라인 실행: `consistency-verifier` → `ai-action` → (`test-verifier` ∥ `compliance-verifier`)
4. 모든 agent PASS 후 구현 커밋 및 push
