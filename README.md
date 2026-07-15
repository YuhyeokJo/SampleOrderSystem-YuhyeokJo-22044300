# SampleOrderSystem

가상의 반도체 회사 **S-Semi**의 반도체 시료(Sample) 생산주문 관리 시스템입니다.
시료 등록부터 주문 접수, 생산, 승인/거절, 출고, 모니터링까지의 흐름을 콘솔(터미널) 환경에서
관리합니다. 개발 원칙은 `CLAUDE.md`를 참고하세요.

## 실행 방법

```bash
python main.py
```

별도의 외부 의존성 없이 표준 라이브러리만 사용하며, `pip install`이 필요하지 않습니다.

실행하면 시료 요약 정보(등록된 시료 종류 수, 전체 재고 수량 합계)와 함께 메인 메뉴가
표시됩니다.

```
1. 시료 관리
2. 시료 주문
3. 주문 승인/거절
4. 모니터링
5. 생산라인
6. 출고 처리
7. 프로그램 종료
```

번호를 선택하면 해당 기능의 하위 메뉴로 진입하며, 하위 메뉴에서 종료를 선택하면 메인 메뉴로
돌아옵니다.

## 테스트 실행

```bash
python -m pytest tests/ -v
```

전체 기능이 콘솔에서 실제로 맞물려 동작하는지는 `tests/test_end_to_end_scenario.py`가
`MainController`를 실제 콘솔 경로 그대로 구동해서 검증한다.

```bash
python -m pytest tests/test_end_to_end_scenario.py -v
```

## 콘솔에서 전체 시나리오 직접 확인하기

`scripts/demo_scenario.txt`에는 더미 시료 등록 → 주문 접수 → 승인/거절 → 생산 완료 → 출고 →
모니터링까지 이어지는 입력값이 한 줄씩 저장되어 있다. 이를 표준입력으로 넣어 `main.py`를
실행하면, 실제 콘솔 화면에 어떻게 출력되는지 눈으로 확인할 수 있다(pytest처럼 값만
assert하는 것이 아니라 실제 렌더링된 표/배지/진행률 바를 그대로 볼 수 있다).

```bash
# bash / git bash
python main.py < scripts/demo_scenario.txt
```

```powershell
# PowerShell
Get-Content scripts\demo_scenario.txt | python main.py
```

시나리오는 시료 2종(S-001 재고100, S-002 재고5) 등록, 주문 3건 접수(재고 충분/부족/거절
대상 각 1건), 승인·거절, 생산 완료, 출고까지 진행한 뒤 최종 모니터링(RELEASE 2건, S-002
재고 고갈 상태)을 보여주고 프로그램을 종료한다. 이 파일과 같은 디렉터리에 `samples.json`,
`orders.json`, `data/` 등 실행 결과 파일이 생성되므로, 실제 프로젝트 데이터에 영향을 주지
않으려면 별도의 빈 디렉터리에서 실행하는 것을 권장한다.

## 주문 상태 흐름

```
RESERVED → (승인) → 재고 충분  → CONFIRMED → RELEASE
                 → 재고 부족  → PRODUCING → CONFIRMED → RELEASE
         → (거절) → REJECTED
```

## 프로젝트 구조

```
SampleOrderSystem-YuhyeokJo-22044300/
├── main.py                        # 엔트리 포인트, MainController를 생성해 실행
├── model/                         # 데이터와 비즈니스 로직 (콘솔 입출력 없음)
│   ├── sample.py                  # Sample 엔티티(시료 ID/이름/평균 생산시간/수율/재고 수량)
│   ├── sample_model.py            # SampleModel: 시료 등록/목록/검색/재고 차감
│   ├── sample_repository.py       # 시료 JSON 영속성(임시파일+os.replace 원자적 저장)
│   ├── order.py                   # Order 엔티티(주문번호/시료ID/고객명/수량/상태)
│   ├── order_model.py             # OrderModel: 주문 접수, 주문번호 채번, 상태별 목록 조회/전환
│   ├── order_repository.py        # 주문 JSON 영속성
│   ├── production_job.py          # ProductionJob 엔티티(생산 큐 항목)
│   ├── production_model.py        # ProductionModel: 생산량 계산, FIFO 큐, 진행 기록, 완료 처리
│   ├── production_repository.py   # 생산 큐 JSON 영속성
│   ├── approval_model.py          # ApprovalModel: 주문 승인(재고 충분/부족 분기)·거절
│   ├── release_model.py           # ReleaseModel: CONFIRMED 주문 출고(RELEASE 전환)
│   └── monitoring_model.py        # MonitoringModel: 상태별 주문 수·시료별 재고 상태 집계
├── view/                          # 콘솔 입출력(print/input)만 담당, 비즈니스 로직 없음
│   ├── sample_view.py
│   ├── order_view.py
│   ├── production_view.py
│   ├── approval_view.py
│   ├── release_view.py
│   ├── monitoring_view.py
│   └── main_menu_view.py
├── controller/                    # 입력 흐름 제어, model과 view 연결
│   ├── sample_controller.py       # 시료 관리(등록/목록조회/검색)
│   ├── order_controller.py        # 시료 주문 접수
│   ├── production_controller.py   # 생산라인(생산 진행 기록, 현황/대기 조회)
│   ├── approval_controller.py     # 주문 승인/거절
│   ├── release_controller.py      # 출고 처리
│   ├── monitoring_controller.py   # 모니터링(주문량/재고량 확인)
│   └── main_controller.py         # 메인 메뉴 라우팅(6개 기능 + 종료)
├── tests/                         # 각 model/controller에 대응하는 단위 테스트(pytest)
├── plans/                         # step별 구현 계획(Plan.md: 전체 계획, Plan-step#.md: 세부 계획)
├── prds/                          # step별 상세 기능 명세(PRD-step#.md)
├── reports/                       # step별 구현 결과 리포트(Report-step#.md)
├── .claude/agents/                # 구현 검증 파이프라인 agent 정의
│   ├── consistency-verifier.md    # 코드 생성 전 PRD/PLAN 문서 정합성 검증
│   ├── ai-action.md                # 코드/테스트 생성, REPORT 작성
│   ├── test-verifier.md            # 테스트 실제 실행 검증
│   └── compliance-verifier.md      # PLAN 체크리스트 대조 검증
├── CLAUDE.md                      # 프로젝트 개발 원칙(step 진행 방식, agent 파이프라인)
└── text.md                        # 기능 명세서 원본(PRD)
```

## 계층별 역할

- **model/**: 데이터와 비즈니스 로직만 담당한다. `print`/`input` 등 콘솔 입출력 코드를
  포함하지 않는다.
- **view/**: 콘솔 입출력(`print`/`input`)만 담당하고 비즈니스 로직을 포함하지 않는다. model이나
  controller를 import하지 않는다.
- **controller/**: 사용자 입력 흐름을 제어하고 model과 view를 연결한다. 저장 로직 자체는
  model에 위임한다.
