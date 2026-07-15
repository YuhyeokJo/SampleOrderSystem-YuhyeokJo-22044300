# Plan-step1.md - 시료 관리 구현 계획

## 목표
시스템의 가장 기본 단위인 시료(Sample)를 등록·조회·검색할 수 있는 기능을 구현한다. 이후
모든 step(주문, 생산, 승인/거절, 출고, 모니터링)은 이번 step에서 만든 시료 데이터를 기반으로
동작하므로, 도메인 모델과 저장 방식을 이 단계에서 확정한다.

## 범위

- 시료 등록: 시료 ID(고유값), 이름, 평균 생산시간(min/ea, 양수), 수율(0.0~1.0),
  초기 재고 수량(0 이상 정수) 입력받아 등록
- 시료 목록 조회: 등록된 모든 시료의 ID/이름/평균 생산시간/수율/현재 재고 수량 출력
- 시료 검색: 이름 기준으로 특정 시료 검색

## 범위 제외 (다음 step 이후)

- 주문 접수/승인/거절, 생산라인, 출고, 모니터링, 메인 메뉴 통합은 이번 step에서 다루지 않는다.
- 시료 수정/삭제는 요구사항에 명시되어 있지 않으므로 구현하지 않는다.

## 참고할 기존 프로젝트 구조

- `ConsoleMVC-YuhyeokJo-22044300`: model(데이터/비즈니스 로직)·view(콘솔 입출력)·
  controller(흐름 제어) 계층 분리 패턴을 따른다.
- `DataPersistence-YuhyeokJo-22044300`: JSON 파일 기반 영속성(임시 파일 작성 후
  `os.replace`로 원자적 교체) 방식을 시료 데이터 저장에 활용할 수 있는지 검토한다.

## 예상 산출물 구조 (예시)

```
model/
  sample.py            # Sample 엔티티, SampleModel(등록/목록/검색)
view/
  sample_view.py        # 시료 관련 콘솔 입출력
controller/
  sample_controller.py  # 시료 관리 메뉴 흐름 제어
tests/
  test_sample_model.py
  (필요 시 test_sample_controller.py 등)
```
※ 정확한 파일 구성은 `prds/PRD-step1.md` 검토 및 ai-action 구현 시 확정한다.

## 검증 체크리스트 (compliance-verifier 대조 기준)

- [ ] Sample 엔티티: 시료 ID, 이름, 평균 생산시간, 수율, 재고 수량 필드 보유
- [ ] 시료 등록 기능 구현 및 유효성 검증(평균 생산시간 > 0, 0.0 ≤ 수율 ≤ 1.0, 재고 수량 ≥ 0 정수,
      시료 ID 고유성)
- [ ] 시료 목록 조회 기능(ID/이름/평균 생산시간/수율/재고 수량 표시) 구현
- [ ] 시료 검색 기능(이름 기준) 구현
- [ ] 각 기능에 대응하는 단위 테스트 작성 및 통과
- [ ] REPORT.md(또는 `reports/Report-step1.md`) 작성

## 다음 절차

1. 이 Plan-step1.md 검토/승인 → 커밋
2. `prds/PRD-step1.md` 작성 → 검토/승인
3. agent 파이프라인 실행: `consistency-verifier` → `ai-action` → (`test-verifier` ∥ `compliance-verifier`)
4. 모든 agent PASS 후 구현 커밋
