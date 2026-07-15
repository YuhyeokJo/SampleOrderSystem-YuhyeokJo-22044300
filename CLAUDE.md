# CLAUDE.md

이 파일은 Claude Code가 이 저장소에서 작업할 때 참고하는 가이드입니다.

## 프로젝트 개요

가상의 반도체 회사 **S-Semi**의 반도체 시료(Sample) 생산주문 관리 시스템입니다.
S-Semi는 다양한 종류의 반도체 시료를 생산하여 연구소, 팹리스(Fabless) 업체, 대학 연구실 등의 고객에게 납품합니다.
시료는 주문이 들어오면 웨이퍼 공정 설비를 통해 제작되고, 검수를 거쳐 고객에게 출고됩니다.
이 시스템은 주문 접수 → 생산 → 검수 → 출고로 이어지는 흐름을 관리합니다.

## 작업 진행 방식 (Step 기반 개발)

1. 모든 구현은 **step 단위**로 진행한다.
2. 각 step 구현을 시작하기 전, 반드시 `plans/Plan-step#.md` 파일을 작성하고 사용자에게 검토를 요청한다.
   검토가 완료(승인)된 이후에만 커밋을 진행한다.
3. step별 세부 구현 시, 각 기능에 대한 상세 내용은 `prds/PRD-step#.md`에 작성한 후 사용자에게 검토를 요청하고, 검토를 받은 후에 구현을 진행한다.
4. 각 step 구현 시, `Plan-step#.md`/`PRD-step#.md`에 명시되지 않은 작업(임의의 기능 추가, 범위 확장, 다음 step 선행 구현 등)은 금지한다.

## Agent 파이프라인

모든 구현은 반드시 `.claude/agents/` 폴더의 agent를 아래 순서와 규칙에 따라 활용한다.

```
consistency-verifier → ai-action → test-verifier
                                 → compliance-verifier (병렬)
```

| 단계 | Agent | 역할 |
| --- | --- | --- |
| 1 | consistency-verifier | 코드 생성 전 PRD/PLAN 문서 간 충돌·누락·모호성 검증 |
| 2 | ai-action | 검증 통과 후 실제 코드 및 단위 테스트 생성, `REPORT.md` 작성 |
| 3 | test-verifier | 생성된 코드의 테스트를 실제 실행하여 동작 정확성 검증 |
| 3 | compliance-verifier | PLAN 체크리스트와 산출물을 항목 단위로 대조하여 누락 검증 (test-verifier와 병렬) |

- `consistency-verifier`가 FAIL이면 구현을 시작하지 않는다.
- `test-verifier` 또는 `compliance-verifier`가 FAIL이면 `ai-action`을 재실행한다.
- 모든 agent가 PASS한 후에만 해당 step 완료로 간주한다.

## 참고 프로젝트

구현 시 아래 기존 프로젝트를 확인하고 필요한 구조/패턴을 활용한다.

- `C:\reviewer\work\project\ConsoleMVC-YuhyeokJo-22044300` — 콘솔 기반 MVC 계층 분리 패턴(model/view/controller)
- `C:\reviewer\work\project\DataMonitor-YuhyeokJo-22044300` — 콘솔 실시간 모니터링/대시보드 구성 방식
- `C:\reviewer\work\project\DataPersistence-YuhyeokJo-22044300` — JSON 기반 데이터 영속성(CRUD, 원자적 파일 저장) 구조
- `C:\reviewer\work\project\DummyDataGenerator-YuhyeokJo-22044300` — 더미 데이터 생성 및 스키마 정의 방식

## 코드 스타일

- 클린 코드 원칙을 준수하여 가독성을 최우선으로 고려한다.
- 계층/모듈의 책임을 명확히 분리하고, 의미가 드러나는 이름을 사용한다.
- 불필요한 추상화나 요청 범위를 벗어난 리팩터링은 지양한다.
