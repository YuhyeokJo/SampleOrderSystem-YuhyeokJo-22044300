# Plan-step7.md - 메인 메뉴 통합 구현 계획

## 목표
지금까지 각 step에서 독립적으로 구현한 6개 기능(시료 관리/시료 주문/주문 승인·거절/모니터링/
생산라인/출고 처리)을 하나의 콘솔 진입점(`main.py`)에서 선택해 실행할 수 있도록 통합한다.
메뉴 화면에는 전체 시료에 대한 요약 정보를 함께 표시한다.

## 요약 정보 표시 방식에 대한 설계 결정

원본 요구사항은 "전체 시료에 대한 요약 정보를 함께 확인할 수 있다"고만 서술하고 구체적인
표시 항목을 정의하지 않는다. 이미 시료 관리 메뉴에서 전체 시료의 상세 목록(ID/이름/평균
생산시간/수율/재고 수량)을 조회할 수 있으므로, 메인 메뉴의 "요약 정보"는 이를 중복하지 않는
간단한 한 줄 요약으로 정의한다: **등록된 시료 종류 수**와 **전체 시료의 재고 수량 합계**를
메인 메뉴 화면 상단에 표시한다. 시료가 하나도 없으면 "등록된 시료 없음"으로 표시한다.

## 범위

- 메인 메뉴: 아래 6개 기능 진입 항목과 종료 항목을 표시한다.
  - 시료 관리, 시료 주문, 주문 승인/거절, 모니터링, 생산라인, 출고 처리, 프로그램 종료
- 메뉴가 표시될 때마다 시료 요약 정보(등록된 시료 종류 수, 전체 재고 수량 합계)를 함께
  표시한다.
- 각 메뉴 항목을 선택하면 해당 기능의 기존 컨트롤러(`SampleController`, `OrderController`,
  `ApprovalController`, `MonitoringController`, `ProductionController`, `ReleaseController`)를
  그대로 실행한다. 각 컨트롤러는 자체적인 종료 옵션을 가지고 있으므로, 해당 컨트롤러가
  종료되면 메인 메뉴로 돌아온다.
- 잘못된 메뉴 선택 시 오류를 안내하고 메인 메뉴를 다시 표시한다.
- `main.py`가 이 메인 메뉴를 프로그램의 유일한 진입점으로 실행하도록 연결한다.

## 범위 제외

- 각 기능(시료 관리, 시료 주문 등)의 내부 로직은 Step 1~6에서 이미 구현되어 있으므로 이번
  step에서 수정하지 않는다. 오직 메뉴 라우팅과 요약 정보 표시만 추가한다.
- 새로운 도메인 기능(재고/주문/생산/승인/출고와 관련된 새로운 동작)은 추가하지 않는다.

## 참고할 기존 프로젝트 구조 및 이전 step 산출물

- `ConsoleMVC-YuhyeokJo-22044300`: model/view/controller 계층 분리 패턴을 그대로 따른다.
- Step 1~6에서 만든 각 컨트롤러(`controller/sample_controller.py`,
  `controller/order_controller.py`, `controller/approval_controller.py`,
  `controller/monitoring_controller.py`, `controller/production_controller.py`,
  `controller/release_controller.py`)를 그대로 재사용한다.
- 요약 정보 계산에는 Step 1의 `SampleModel.all()`을 재사용한다.

## 예상 산출물 구조 (예시)

```
view/
  main_menu_view.py        # 메인 메뉴 콘솔 입출력(요약 정보 + 메뉴 표시)
controller/
  main_controller.py        # MainController(메뉴 라우팅, 각 기능 컨트롤러 실행)
main.py                     # (수정) MainController를 실행하도록 변경
tests/
  test_main_controller.py
```
※ 정확한 파일 구성은 `prds/PRD-step7.md` 검토 및 ai-action 구현 시 확정한다.

## 검증 체크리스트 (compliance-verifier 대조 기준)

- [ ] 메인 메뉴에 6개 기능 항목 + 종료 항목이 모두 표시됨
- [ ] 메뉴 표시 시 시료 요약 정보(등록된 시료 종류 수, 전체 재고 수량 합계)가 함께 표시됨,
      시료가 없으면 "등록된 시료 없음" 표시
- [ ] 각 메뉴 항목 선택 시 대응하는 기존 컨트롤러가 실행되고, 해당 컨트롤러 종료 후 메인
      메뉴로 복귀함
- [ ] 잘못된 선택 시 오류 안내 후 메인 메뉴 재표시
- [ ] `main.py`가 메인 메뉴를 유일한 진입점으로 실행하도록 연결됨
- [ ] Step 1~6의 기존 기능 코드가 수정되지 않음(라우팅 코드만 추가)
- [ ] 각 기능에 대응하는 단위 테스트 작성 및 통과
- [ ] REPORT.md(또는 `reports/Report-step7.md`) 작성

## 다음 절차

1. 이 Plan-step7.md 검토/승인 → 커밋
2. `prds/PRD-step7.md` 작성 → 검토/승인
3. agent 파이프라인 실행: `consistency-verifier` → `ai-action` → (`test-verifier` ∥ `compliance-verifier`)
4. 모든 agent PASS 후 구현 커밋 및 push
