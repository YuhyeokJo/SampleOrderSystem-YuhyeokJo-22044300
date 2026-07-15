# Plan-step2.md - 시료 주문 접수 구현 계획

## 목표
고객의 시료 요청을 주문 담당자가 주문으로 접수하는 기능을 구현한다. 이번 step에서 만드는
Order 데이터와 상태 값(RESERVED)은 이후 step(주문 승인/거절, 생산라인, 출고, 모니터링)이
공통으로 참조하는 기반이 되므로, 주문 도메인 모델과 상태 값을 이 단계에서 확정한다.

## 범위

- 시료 예약(주문 접수): 시료 ID, 고객명, 주문 수량을 입력받아 주문을 생성한다.
- 접수된 주문은 상태값 `RESERVED`로 설정된다.
- 주문번호는 `ORD-YYYYMMDD-XXXX` 형식으로 자동 생성된다.
- 주문 대상 시료는 시스템에 등록되어 있어야 하며(Step 1의 시료 데이터 참조), 등록되지 않은
  시료 ID로는 주문할 수 없다.
- 접수된 주문 목록을 조회할 수 있다(Step 1의 시료 목록 조회에 대응하는 주문 조회 기능).

## 범위 제외 (다음 step 이후)

- 주문 승인/거절 처리(재고 판단, CONFIRMED/PRODUCING/REJECTED 전환)는 Step 4에서 다룬다.
- 생산라인, 출고, 모니터링, 메인 메뉴 통합은 이번 step에서 다루지 않는다.
- 주문 수정/취소는 요구사항에 명시되어 있지 않으므로 구현하지 않는다.

## 참고할 기존 프로젝트 구조 및 Step 1 산출물

- `ConsoleMVC-YuhyeokJo-22044300`: model/view/controller 계층 분리 패턴을 그대로 따른다.
- `DataPersistence-YuhyeokJo-22044300`: JSON 파일 기반 영속성(임시 파일 작성 후 `os.replace`
  원자적 교체) 방식을 주문 데이터 저장에도 동일하게 적용한다.
- Step 1 산출물(`model/sample_model.py`, `model/sample_repository.py`)의 시료 조회 기능을
  재사용하여 주문 대상 시료의 존재 여부를 검증한다.

## 예상 산출물 구조 (예시)

```
model/
  order.py              # Order 엔티티
  order_repository.py    # 주문 JSON 영속성 (원자적 저장)
  order_model.py         # OrderModel(주문 접수/조회, 주문번호 채번)
view/
  order_view.py          # 주문 관련 콘솔 입출력
controller/
  order_controller.py    # 시료 주문 메뉴 흐름 제어
tests/
  test_order_model.py
  test_order_repository.py
  test_order_controller.py
```
※ 정확한 파일 구성은 `prds/PRD-step2.md` 검토 및 ai-action 구현 시 확정한다.

## 검증 체크리스트 (compliance-verifier 대조 기준)

- [ ] Order 엔티티: 주문번호, 시료 ID, 고객명, 주문 수량, 상태(RESERVED) 필드 보유
- [ ] 주문번호 자동 생성 기능(`ORD-YYYYMMDD-XXXX` 형식) 구현
- [ ] 시료 예약(주문 접수) 기능 구현 및 유효성 검증(등록되지 않은 시료 ID로 주문 불가, 주문 수량
      양의 정수)
- [ ] 접수된 주문은 상태값 RESERVED로 저장됨
- [ ] 접수된 주문 목록 조회 기능 구현
- [ ] JSON 파일 기반 영속성 적용(재시작 후에도 주문 데이터 유지)
- [ ] 각 기능에 대응하는 단위 테스트 작성 및 통과
- [ ] REPORT.md(또는 `reports/Report-step2.md`) 작성

## 다음 절차

1. 이 Plan-step2.md 검토/승인 → 커밋
2. `prds/PRD-step2.md` 작성 → 검토/승인
3. agent 파이프라인 실행: `consistency-verifier` → `ai-action` → (`test-verifier` ∥ `compliance-verifier`)
4. 모든 agent PASS 후 구현 커밋 및 push
