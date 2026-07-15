# Plan-step5.md - 출고 처리 구현 계획

## 목표
재고가 충분해져 승인 완료된(CONFIRMED) 주문에 대해 출고를 처리하는 기능을 구현한다. Step 2/4의
`OrderModel`을 확장해 CONFIRMED 목록 조회와 출고(RELEASE 전환) 기능을 추가한다.

## 범위

- CONFIRMED 상태의 주문 목록 조회: 상태가 `CONFIRMED`인 주문만 표시한다.
- 출고 처리: 담당자가 CONFIRMED 목록에서 특정 주문을 선택해 출고를 실행하면, 해당 주문 상태를
  `RELEASE`로 전환한다.
- 출고 대상 주문은 반드시 `CONFIRMED` 상태여야 하며, 그렇지 않은 주문(예: RESERVED, PRODUCING,
  REJECTED, 이미 RELEASE된 주문)에 대한 출고 시도는 거부한다.

## 범위 제외

- 재고, 생산라인, 승인/거절 로직은 Step 1/3/4에서 이미 구현되어 있으므로 이번 step에서 다루지
  않는다(출고는 상태 전환만 수행하며 재고에 영향을 주지 않는다 — 재고는 이미 Step 4 승인
  시점에 소비 처리됨).
- 모니터링, 메인 메뉴 통합은 이번 step에서 다루지 않는다.

## 참고할 기존 프로젝트 구조 및 이전 step 산출물

- `ConsoleMVC-YuhyeokJo-22044300`: model/view/controller 계층 분리 패턴을 그대로 따른다.
- Step 2/4 산출물(`model/order_model.py`)에 CONFIRMED 목록 조회 기능을 추가하고,
  `update_status`/`find_by_id`를 재사용해 상태를 전환한다.

## 예상 산출물 구조 (예시)

```
model/
  order_model.py           # (수정) CONFIRMED 목록 조회 기능 추가
  release_model.py          # ReleaseModel(CONFIRMED 목록 조회, 출고 처리)
view/
  release_view.py            # 출고 관련 콘솔 입출력
controller/
  release_controller.py      # 출고 처리 메뉴 흐름 제어
tests/
  test_order_model.py        # (수정) CONFIRMED 목록 조회 테스트 추가
  test_release_model.py
  test_release_controller.py
```
※ 정확한 파일 구성은 `prds/PRD-step5.md` 검토 및 ai-action 구현 시 확정한다.

## 검증 체크리스트 (compliance-verifier 대조 기준)

- [ ] `OrderModel`에 CONFIRMED 상태 주문 목록 조회 기능 추가
- [ ] CONFIRMED 주문 목록 조회 기능 구현(CONFIRMED만 표시, 없으면 안내)
- [ ] 출고 처리 기능 구현: 대상 주문이 CONFIRMED가 아니면 거부
- [ ] 출고 처리 성공 시 주문 상태가 RELEASE로 전환됨
- [ ] JSON 파일 기반 영속성 적용(재시작 후에도 출고된 주문 상태 유지)
- [ ] 각 기능에 대응하는 단위 테스트 작성 및 통과
- [ ] REPORT.md(또는 `reports/Report-step5.md`) 작성

## 다음 절차

1. 이 Plan-step5.md 검토/승인 → 커밋
2. `prds/PRD-step5.md` 작성 → 검토/승인
3. agent 파이프라인 실행: `consistency-verifier` → `ai-action` → (`test-verifier` ∥ `compliance-verifier`)
4. 모든 agent PASS 후 구현 커밋 및 push
