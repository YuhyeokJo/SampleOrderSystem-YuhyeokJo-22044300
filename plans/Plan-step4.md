# Plan-step4.md - 주문 승인/거절 구현 계획

## 목표
접수된(RESERVED) 주문 목록을 확인하고, 재고 상황에 따라 자동으로 승인 처리(재고 충분 시
즉시 CONFIRMED, 재고 부족 시 생산라인에 등록 후 PRODUCING)하거나 거절(REJECTED)하는 기능을
구현한다. Step 1(시료 재고)과 Step 3(생산라인)의 산출물을 조합해 실제 승인 흐름을 완성하는
단계다.

## 재고 차감 관련 설계 결정

- 원본 요구사항은 재고 충분/부족 판단 기준만 제시하고 있으나, 승인이 실제로 재고를 소비하는
  행위이므로 이번 step에서 `SampleModel`에 재고를 차감하는 기능을 추가한다.
- **재고 충분**(시료 재고 ≥ 주문 수량): 주문 수량만큼 재고를 차감하고 주문 상태를 즉시
  `CONFIRMED`로 전환한다.
- **재고 부족**(시료 재고 < 주문 수량): 남아 있는 재고 전량을 차감(재고를 0으로 소진)하고,
  부족분(주문 수량 − 기존 재고)만큼을 Step 3의 생산라인에 등록한 뒤 주문 상태를 `PRODUCING`으로
  전환한다. 생산라인이 처리해 채워주는 부족분은 해당 주문 전용으로 소비되는 것으로 간주하며,
  생산 완료 시(Step 3에서 이미 구현됨) 시료의 일반 재고 수량에는 반영하지 않는다(생산라인 정의
  6절: "주문이 들어온 시료에 대해서만 생산"이라는 전용 생산 개념에 따른 해석).
- 생산라인 등록이 실패하는 경우(예: Step 3에서 정의한 대로 시료 수율이 정확히 0.0이어서 생산
  자체가 불가능한 경우)에는 승인 처리 전체를 되돌린다: 재고 차감을 적용하지 않고 주문 상태도
  변경하지 않은 채 오류를 안내한다.

## 범위

- 접수된 주문 목록 조회: RESERVED 상태의 주문만 표시(Step 2에서 이관됨).
- 주문 승인: RESERVED 상태의 주문만 승인 가능. 재고 충분/부족 판단 후 위 설계 결정에 따라
  처리한다. RESERVED가 아닌 주문을 승인하려 하면 거부한다.
- 주문 거절: RESERVED 상태의 주문만 거절 가능하며, 즉시 `REJECTED`로 전환한다. RESERVED가
  아닌 주문을 거절하려 하면 거부한다.

## 범위 제외 (다음 step 이후)

- 생산 현황/대기 주문 조회, 생산 진행 기록 자체는 Step 3에서 이미 구현되어 있으므로 이번
  step에서 다시 다루지 않는다(생산라인 등록만 이번 step에서 호출).
- 출고 처리, 모니터링, 메인 메뉴 통합은 이번 step에서 다루지 않는다.

## 참고할 기존 프로젝트 구조 및 이전 step 산출물

- `ConsoleMVC-YuhyeokJo-22044300`: model/view/controller 계층 분리 패턴을 그대로 따른다.
- Step 1 산출물(`model/sample_model.py`): 시료 조회 기능을 재사용하고, 재고 차감 기능을
  추가한다.
- Step 2 산출물(`model/order_model.py`): RESERVED 주문 목록 조회 기능을 추가하고,
  Step 3에서 추가된 `update_status`/`find_by_id`를 재사용해 상태를 전환한다.
- Step 3 산출물(`model/production_model.py`): 생산 큐 등록 기능(`register` 등)을 재사용해
  재고 부족분을 생산라인에 등록한다.

## 예상 산출물 구조 (예시)

```
model/
  sample_model.py          # (수정) 재고 차감 기능 추가
  order_model.py           # (수정) RESERVED 목록 조회 기능 추가
  approval_model.py         # ApprovalModel(승인/거절 처리, 재고 판단 및 각 모델 조합)
view/
  approval_view.py           # 접수된 주문 목록/승인/거절 관련 콘솔 입출력
controller/
  approval_controller.py     # 주문 승인/거절 메뉴 흐름 제어
tests/
  test_sample_model.py       # (수정) 재고 차감 테스트 추가
  test_order_model.py        # (수정) RESERVED 목록 조회 테스트 추가
  test_approval_model.py
  test_approval_controller.py
```
※ 정확한 파일 구성은 `prds/PRD-step4.md` 검토 및 ai-action 구현 시 확정한다.

## 검증 체크리스트 (compliance-verifier 대조 기준)

- [ ] `SampleModel`에 재고 차감 기능 추가(차감 후 음수가 되지 않도록 보장)
- [ ] `OrderModel`에 RESERVED 상태 주문 목록 조회 기능 추가
- [ ] 접수된 주문 목록 조회 기능 구현(RESERVED만 표시)
- [ ] 주문 승인 기능 구현: RESERVED가 아니면 거부
- [ ] 재고 충분 시 재고 차감 + 즉시 CONFIRMED 전환 구현
- [ ] 재고 부족 시 재고 전량 차감 + 부족분 생산라인 등록(Step 3 `ProductionModel` 재사용) +
      PRODUCING 전환 구현
- [ ] 생산라인 등록 실패 시(수율 0.0 등) 재고 차감/상태 변경 없이 승인 전체 취소 및 오류 안내
- [ ] 주문 거절 기능 구현: RESERVED가 아니면 거부, RESERVED면 즉시 REJECTED 전환
- [ ] JSON 파일 기반 영속성 적용(재시작 후에도 재고/주문/생산 큐 데이터 유지)
- [ ] 각 기능에 대응하는 단위 테스트 작성 및 통과
- [ ] REPORT.md(또는 `reports/Report-step4.md`) 작성

## 다음 절차

1. 이 Plan-step4.md 검토/승인 → 커밋
2. `prds/PRD-step4.md` 작성 → 검토/승인
3. agent 파이프라인 실행: `consistency-verifier` → `ai-action` → (`test-verifier` ∥ `compliance-verifier`)
4. 모든 agent PASS 후 구현 커밋 및 push
