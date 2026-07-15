# Plan-step8.md - 콘솔 UI 개선 구현 계획

## 배경 및 목표
지금까지 구현한 콘솔 출력
형식을 구분선·정렬된 표·상태 배지·진행률 바 등을 갖춘 스타일로 개선한다. 이번 step은
**view 계층의 출력 포맷팅만** 개선하며, model/controller의 비즈니스 로직이나 기존 메서드
시그니처는 변경하지 않는다(순수 UI 개선).

## 설계 결정

### 1. 공통 포맷 헬퍼 도입
7개 view 파일(`sample_view.py`, `order_view.py`, `approval_view.py`, `production_view.py`,
`release_view.py`, `monitoring_view.py`, `main_menu_view.py`)에 반복되는 구분선/표/배지
렌더링 코드를 하나의 공통 모듈로 추출한다: `view/console_format.py`
- `render_divider(width=64)`: `"=" * width` 형태의 구분선 문자열 반환
- `render_table(headers, rows, aligns)`: 헤더/행 데이터를 열 폭에 맞춰 정렬한 표 문자열
  목록 반환(각 view의 컬럼 폭 하드코딩을 대체)
- `render_status_badge(status)`: 상태값을 `[RESERVED]`처럼 대괄호로 감싸 표기
- `render_progress_bar(current, total, width=20)`: `current/total` 비율을 채움 문자로
  표현한 진행률 바 문자열(예: `[██████░░░░] 60%`) 반환. `total`이 0이면 빈 바(0%)를 반환한다.

### 2. 화면별 개선 범위
- **메인 메뉴**: 상단에 `render_divider()`로 구분선을 두르고, "S-Semi 반도체 시료
  생산주문관리 시스템" 배너와 "시스템 현황" 라벨을 표시한다. 요약 정보 항목은 **Step 7에서
  확정한 내용(등록된 시료 종류 수, 총 재고 수량)을 그대로 유지**하며, 이번 step에서 새로운
  집계 항목(전체 주문 건수, 생산라인 대기 건수 등)을 추가하지 않는다(아래 "범위 제외" 참고).
  메뉴 항목은 `[1] 시료 관리` 형식으로 번호를 대괄호로 표기하고, 입력 프롬프트를
  `선택 > `로 통일한다.
- **시료 관리**: 목록/검색 결과를 `render_table`로 정렬하고, 목록 상단에
  "등록 시료 목록 (총 N종)"처럼 건수를 표시한다.
- **시료 주문**: 입력받은 시료 ID/고객명/주문 수량을 저장 전에 다시 한번 요약해 보여주는
  "입력 내용 확인" 블록을 추가한다(입력값을 그대로 나열만 하며, 승인/취소를 묻는 추가
  확인 단계는 추가하지 않는다 — 아래 "범위 제외" 참고). 접수 성공 시 주문번호와 상태
  배지(`[RESERVED]`)를 표시한다.
- **주문 승인/거절**: RESERVED 목록을 번호가 매겨진 표로 표시하고, 승인 처리 결과에 상태
  전이(`RESERVED → [CONFIRMED]` 또는 `RESERVED → [PRODUCING]`, 부족분이 있으면 부족분
  수량 표시)를 함께 보여준다. 이 정보는 기존 `ApprovalModel.approve()`가 이미 반환하는
  `(주문, 부족분 또는 None)` 값만으로 구성하며, 생산량/생산시간 미리보기처럼 모델에 없는
  정보를 새로 계산하지 않는다.
- **생산라인**: 생산 현황 조회 시 누적 생산량/실 생산량을 `render_progress_bar`로 시각화한다
  (완료 예정 시각처럼 현재 데이터 모델에 없는 값은 표시하지 않는다).
- **출고 처리**: CONFIRMED 목록을 표로 표시하고, 출고 완료 시 상태 전이
  (`CONFIRMED → [RELEASE]`)를 표시한다.
- **모니터링**: 상태별 주문 건수를 상태 배지와 함께 표시하고, 재고 현황 표에 상태 배지
  (`[여유]`/`[부족]`/`[고갈]`)를 적용한다. PDF 예시의 "잔여율" 막대 그래프는 이 시스템에
  정의된 적 없는 지표(재고의 기준 최대치가 정의되어 있지 않음)이므로 도입하지 않는다.

## 범위 제외 (이번 step에서 다루지 않음)

- 메인 메뉴 요약 정보에 새로운 집계 항목(전체 주문 건수, 생산라인 대기 건수 등) 추가 —
  Step 7에서 이미 확정·검증된 요약 항목 구성을 변경하지 않는다.
- 시료 주문 접수 시 `[Y] 예약 접수 / [N] 취소`와 같은 추가 확인 단계 도입 — 기존 접수
  흐름(입력 → 즉시 처리)을 변경하지 않는다.
- 승인 처리 전에 실 생산량/총 생산 시간을 미리 계산해 보여주는 기능 — `ApprovalModel`이
  현재 이 값을 반환하지 않으므로, 모델 변경 없이는 표시할 수 없다.
- 모니터링의 재고 "잔여율" 퍼센트 바, 생산 현황의 "완료 예정 시각" — 정의되지 않은 지표라
  임의로 계산해 표시하지 않는다.
- ANSI 색상 코드 적용 — 터미널 환경에 따라 깨질 수 있어 이번 step에서는 문자 기반 배지
  (`[RESERVED]` 등)로만 표기하고 실제 색상은 적용하지 않는다.
- model/controller의 비즈니스 로직, 메서드 시그니처, 저장 방식 변경 — 이번 step은
  view 계층 출력 포맷팅만 대상으로 한다.

## 참고할 기존 프로젝트 구조

- `DataMonitor-YuhyeokJo-22044300`: 콘솔에서 상태를 표 형태로 정리해 보여주는 방식을
  참고한다(단, 실시간 감시(watchdog)는 가져오지 않는다 — 이미 Step 6에서도 동일하게
  결정한 사항).

## 예상 산출물 구조 (예시)

```
view/
  console_format.py         # 신규: 구분선/표/배지/진행률 바 공통 렌더링 헬퍼
  sample_view.py             # (수정) 공통 헬퍼 사용, 출력 포맷 개선
  order_view.py               # (수정)
  approval_view.py            # (수정)
  production_view.py          # (수정)
  release_view.py             # (수정)
  monitoring_view.py          # (수정)
  main_menu_view.py           # (수정)
tests/
  test_console_format.py      # 신규: 공통 헬퍼 단위 테스트
  test_sample_view.py         # 신규: 각 view의 실제 출력(print) 검증(capsys)
  test_order_view.py
  test_approval_view.py
  test_production_view.py
  test_release_view.py
  test_monitoring_view.py
  test_main_menu_view.py
```
※ 정확한 파일 구성은 `prds/PRD-step8.md` 검토 및 ai-action 구현 시 확정한다.

## 검증 체크리스트 (compliance-verifier 대조 기준)

- [ ] `view/console_format.py`에 구분선/표/상태 배지/진행률 바 렌더링 함수 구현
- [ ] 7개 view 파일이 모두 공통 헬퍼를 사용하도록 개선됨
- [ ] 메인 메뉴 요약 정보 항목이 Step 7과 동일(시료 종류 수, 총 재고)하게 유지됨(집계
      항목 추가 없음)
- [ ] 시료 주문 접수 흐름에 추가 확인 단계(Y/N)가 도입되지 않음(범위 제외 준수)
- [ ] 승인/거절, 출고 처리 시 상태 전이가 상태 배지로 표시됨
- [ ] 생산 현황 조회 시 누적 생산량/실 생산량이 진행률 바로 표시됨
- [ ] 모니터링 재고 현황에 상태 배지가 적용되고, 정의되지 않은 "잔여율" 지표는 도입되지
      않음
- [ ] model/controller의 기존 로직·시그니처·저장 방식이 전혀 수정되지 않음(view 계층만
      변경)
- [ ] 기존 controller 단위 테스트(FakeView 기반)가 필요한 만큼만 갱신된 뒤(FakeView에 신규
      메서드 추가, 출력 문자열 검사를 view 메서드 호출/인자 검사로 변경) 전부 통과함(검증
      대상인 "어떤 model 호출 결과가 사용자에게 전달되는가"는 이전과 동일하게 유지, 회귀 없음)
- [ ] 각 view의 실제 출력에 대한 신규 단위 테스트 작성 및 통과
- [ ] REPORT.md(또는 `reports/Report-step8.md`) 작성

## 다음 절차

1. 이 Plan-step8.md 검토/승인 → 커밋
2. `prds/PRD-step8.md` 작성(화면별 정확한 출력 포맷 명세) → 검토/승인
3. agent 파이프라인 실행: `consistency-verifier` → `ai-action` → (`test-verifier` ∥ `compliance-verifier`)
4. 모든 agent PASS 후 구현 커밋 및 push
