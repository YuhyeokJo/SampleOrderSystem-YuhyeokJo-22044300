# PRD-step8.md - 콘솔 UI 개선 기능 명세

## 개요
Plan-step8.md에서 정한 범위에 따라, 콘솔 출력 형식을 구분선·정렬된 표·상태 배지·진행률
바를 갖춘 스타일로 개선한다. model의 판단 로직, 저장 방식, 호출 순서는 전혀 변경하지
않는다.

## controller 변경 범위에 대한 명확화 (중요)
Plan-step8.md는 "view 계층 출력 포맷팅만 개선"을 원칙으로 하지만, 현재 일부 controller
(`sample_controller.py`, `order_controller.py`, `approval_controller.py`,
`production_controller.py`, `release_controller.py`)는 성공/실패 메시지를 f-string으로
직접 조합한 뒤 `view.show_message(text)`를 호출하고 있다. 이런 메시지에 상태 배지를
적용하려면 그 문구 조립 책임을 view로 옮겨야 하므로, 아래 두 가지 종류의 controller 수정만
예외적으로 허용한다.

- **허용**: `self.view.show_message(f"...")` 형태로 문자열을 직접 조립해 전달하던 코드를,
  같은 시점에 이미 가지고 있는 도메인 객체(예: 갱신된 `Order`, `ProductionJob`)를 그대로
  넘기는 `self.view.show_xxx_result(order)`와 같은 새 view 메서드 호출로 교체하는 것.
- **금지**: model 메서드 호출 순서, 호출 대상, 분기 조건(if/else) 등 어떤 판단 로직도
  변경하지 않는다. 즉 controller의 "무엇을 언제 호출하는가"는 그대로 두고, "그 결과를 어떤
  문자열로 보여주는가"만 view로 위임한다.
- 이 위임 방식 변경으로 인해 기존 controller 단위 테스트의 `FakeView`(테스트 더블)에도
  새 메서드가 추가되어야 한다. 또한 기존 테스트 중 `show_message`로 전달된 문자열 내용을
  직접 검사하던 assertion(예: `"PRODUCING" in message`처럼 메시지 텍스트를 확인하던 부분)은,
  해당 결과가 `show_xxx_result(order, ...)` 같은 새 메서드 호출로 옮겨간 경우 "그 메서드가
  올바른 인자(`order`, `shortage_quantity` 등)로 호출되었는지"를 확인하는 assertion으로
  고쳐 써야 한다. 이는 테스트 파일을 건드리지 않는 것이 아니라, 검증 대상을 "출력 문자열"에서
  "view 메서드 호출 여부/인자"로 옮기는 예상된 리팩터링이며, 검증하는 대상(어떤 model
  호출 결과가 사용자에게 전달되는지)은 동일하게 유지된다.

## `view/console_format.py` (신규 공통 헬퍼)

| 함수 | 시그니처 | 동작 |
|---|---|---|
| `render_divider` | `render_divider(width=64)` | `"=" * width` 문자열 반환 |
| `render_table` | `render_table(headers, rows, aligns)` | `headers`: 컬럼명 리스트, `rows`: 각 행이 문자열로 변환 가능한 값의 리스트인 2차원 리스트, `aligns`: `headers`와 길이가 같은 정렬 지정 리스트(각 원소는 `"<"`(좌측 정렬) 또는 `">"`(우측 정렬)). 각 컬럼 폭을 헤더/데이터 중 가장 긴 길이 + 2칸 여백으로 계산하고, 해당 컬럼의 `aligns` 값에 따라 좌/우 정렬한 문자열 리스트(헤더 1줄 + 데이터 N줄)를 반환한다. `rows`가 비어 있으면 헤더만 반환한다. `aligns`의 길이가 `headers`와 다르면 `ValueError`를 발생시킨다. |
| `render_status_badge` | `render_status_badge(status)` | `f"[{status}]"` 반환 |
| `render_progress_bar` | `render_progress_bar(current, total, width=20)` | `total <= 0`이면 `f"[{'░' * width}] 0%"` 반환. 그렇지 않으면 `filled = round(width * current / total)`(0~width로 clamp), `percent = round(current / total * 100)`으로 `f"[{'█' * filled}{'░' * (width - filled)}] {percent}%"` 반환. |

## 화면별 출력 포맷 명세

### 1. 메인 메뉴 (`main_menu_view.py`)
- `show_summary(sample_count, total_stock_quantity)`:
  - `sample_count == 0`: `"등록된 시료가 없습니다."` 한 줄 출력(기존과 동일한 문구, 변경 없음).
  - 그 외: `"등록된 시료: {sample_count}종"`과 `"총 재고 수량: {total_stock_quantity}"`을 각각
    한 줄씩 출력(기존과 동일, 문구 변경 없음 — Step 7에서 확정된 내용이므로 유지).
- `show_menu()`: 아래 형식으로 출력한다(구분선 + 배너 + 메뉴 항목).
  ```
  ============================================================
   S-Semi 반도체 시료 생산주문관리 시스템
  ============================================================
   [1] 시료 관리          [2] 시료 주문
   [3] 주문 승인/거절       [4] 모니터링
   [5] 생산라인            [6] 출고 처리
   [7] 프로그램 종료
  ------------------------------------------------------------
  ```
- `prompt_choice()`: 입력 프롬프트 문구를 `"선택 > "`로 변경한다(기존 `"메뉴를 선택하세요: "`
  대체).

### 2. 시료 관리 (`sample_view.py`)
- `show_menu()`: 상단에 `render_divider()`와 `" [1] 시료 관리"` 제목을 추가하고, 메뉴 항목은
  `[1] 시료 등록  [2] 시료 목록 조회  [3] 시료 검색  [4] 종료` 한 줄로 표기한다.
- `prompt_choice()`: `"선택 > "`로 통일한다.
- `show_samples(samples)`:
  - 비어 있으면 기존과 동일하게 `"등록된 시료가 없습니다."` 출력(변경 없음).
  - 그 외: `f"등록 시료 목록 (총 {len(samples)}종)"` 한 줄을 출력한 뒤,
    `render_table(["시료 ID", "이름", "평균 생산시간", "수율", "현재 재고"], rows, aligns)`로
    만든 표를 출력한다. `aligns = ["<", "<", ">", ">", ">"]`(시료 ID/이름은 좌측 정렬,
    평균 생산시간/수율/현재 재고는 우측 정렬 — 기존 `COLUMN_HEADER`의 정렬과 동일).

### 3. 시료 주문 (`order_view.py`)
- `show_menu()`: 시료 관리와 동일한 패턴(구분선 + 제목 + 한 줄 메뉴)으로 변경한다.
- `prompt_choice()`: `"선택 > "`로 통일한다.
- controller(`order_controller.py`)에서 시료 ID/고객명/주문 수량을 입력받은 직후, 저장을
  시도하기 전에 `self.view.show_input_summary(sample_id, customer_name, quantity)`를
  호출해 아래와 같이 입력값을 재확인시켜준다(승인/취소를 묻지 않고 정보 제공만 한다 —
  Plan-step8.md의 범위 제외에 따라 흐름을 막는 확인 단계는 추가하지 않는다):
  ```
  입력 내용 확인
   시료 ID  : S-001
   고객명   : 삼성전자 파운드리
   주문 수량 : 200
  ```
- 접수 성공 시, controller는 기존처럼 `Order` 객체를 이미 가지고 있으므로
  `self.view.show_reservation_success(order)`를 호출하고, view는 다음과 같이 출력한다:
  ```
  예약 접수 완료.
   주문번호 : ORD-20260416-0001
   상태     : [RESERVED]
  ```
- 접수 실패 시에는 기존과 동일하게 `f"접수 실패: {error}"` 형태의 메시지를
  `show_message`로 출력한다(실패 메시지는 상태 배지가 필요 없으므로 변경하지 않는다).

### 4. 주문 승인/거절 (`approval_view.py`)
- `show_menu()`: 시료 관리와 동일한 패턴으로 변경한다.
- `show_reserved_orders(orders)`: 비어 있으면 기존과 동일한 안내 문구 유지. 그 외에는
  `f"접수된 주문 목록 (RESERVED, 총 {len(orders)}건)"`을 출력한 뒤, 각 행 앞에 1부터
  시작하는 순번을 붙인
  `render_table(["번호", "주문번호", "시료 ID", "고객명", "주문수량", "상태"], rows, aligns)`
  표를 출력한다. `aligns = ["<", "<", "<", "<", ">", ">"]`(번호/주문번호/시료 ID/고객명은
  좌측 정렬, 주문수량/상태는 우측 정렬 — 기존 `COLUMN_HEADER`의 정렬과 동일하고 번호 컬럼만
  좌측 정렬로 추가). 이 순번은 표시용일 뿐이며, 주문 선택은 기존과 동일하게 주문번호를 직접
  입력하는 방식(`prompt_order_id()`)을 그대로 사용한다(선택 방식은 변경하지 않는다).
- 승인 성공 시, controller는 `ApprovalModel.approve()`가 반환한 `(order, shortage_quantity)`를
  그대로 `self.view.show_approval_result(order, shortage_quantity)`에 전달한다:
  - `shortage_quantity is None`(재고 충분): 
    ```
    승인 완료.
     주문번호   : ORD-...
     상태 변경  : RESERVED → [CONFIRMED]
    ```
  - `shortage_quantity`가 있는 경우(재고 부족):
    ```
    승인 완료.
     주문번호   : ORD-...
     상태 변경  : RESERVED → [PRODUCING]
     부족분     : {shortage_quantity} (생산라인에 등록되었습니다)
    ```
- 거절 성공 시, controller는 갱신된 `Order`를 `self.view.show_rejection_result(order)`에
  전달하고, view는 다음과 같이 출력한다:
  ```
  거절 완료.
   주문번호   : ORD-...
   상태 변경  : RESERVED → [REJECTED]
  ```
- 승인/거절 실패 메시지는 기존과 동일하게 `f"승인 실패: {error}"` / `f"거절 실패: {error}"`를
  `show_message`로 출력한다(변경 없음).

### 5. 생산라인 (`production_view.py`)
- `show_menu()`: 시료 관리와 동일한 패턴으로 변경한다.
- `show_current_job(job)`:
  - `job is None`: 기존과 동일하게 `"진행 중인 생산 항목이 없습니다."` 출력(변경 없음).
  - 그 외:
    ```
    현재 생산 중
     주문번호    : ORD-...
     시료 ID     : S-003
     부족분      : 170
     실 생산량   : 206      총 생산 시간 : 165
     진행률      : [████████████░░░░░░░░] 60% (124/206)
    ```
    진행률 줄은 `render_progress_bar(job.produced_quantity, job.actual_production_quantity)`로
    생성한 문자열과 `"({produced_quantity}/{actual_production_quantity})"`를 붙여 구성한다.
- `show_waiting_jobs(jobs)`: 비어 있으면 기존과 동일한 안내 문구 유지. 그 외에는
  `f"대기 중인 생산 항목 (총 {len(jobs)}건, FIFO)"`을 출력한 뒤 1부터 시작하는 순번을 포함한
  `render_table(["순번", "주문번호", "시료 ID", "부족분", "실 생산량", "총 생산 시간"], rows, aligns)`
  표를 출력한다. `aligns = ["<", "<", "<", ">", ">", ">"]`(순번/주문번호/시료 ID는 좌측 정렬,
  부족분/실 생산량/총 생산 시간은 우측 정렬 — 기존 `COLUMN_HEADER`의 정렬과 동일하고 순번
  컬럼만 좌측 정렬로 추가).
- 등록 성공 시, controller는 `self.view.show_registration_success(job)`을 호출하고, view는
  `f"생산 큐 등록 완료. 실 생산량: {job.actual_production_quantity}, 총 생산 시간: {job.total_production_time}"`
  형태(기존 문구와 동일한 내용, 문구 자체는 변경하지 않음)로 출력한다. 이 항목은 새 메서드로
  옮기되 문구는 그대로 유지한다.
- 진행 기록 결과 출력 시, controller는 `self.view.show_progress_result(job, completed)`를
  호출한다:
  - `completed`가 True: `f"생산 완료: 주문번호 {job.order_id}, 상태 변경: PRODUCING → [CONFIRMED]"`
  - `completed`가 False:
    `"진행 기록 완료: "` + `render_progress_bar(job.produced_quantity, job.actual_production_quantity)`
    + `f" ({job.produced_quantity}/{job.actual_production_quantity})"`

### 6. 출고 처리 (`release_view.py`)
- `show_menu()`: 시료 관리와 동일한 패턴으로 변경한다.
- `show_confirmed_orders(orders)`: 접수된 주문 목록과 동일한 방식(비어있으면 기존 문구 유지,
  그 외에는 건수 안내 + 순번 포함 표)으로 변경한다. 헤더:
  `["번호", "주문번호", "시료 ID", "고객명", "주문수량", "상태"]`,
  `aligns = ["<", "<", "<", "<", ">", ">"]`(접수된 주문 목록과 동일한 정렬 규칙).
- 출고 성공 시, controller는 갱신된 `Order`를 `self.view.show_release_result(order)`에
  전달하고 view는 다음과 같이 출력한다:
  ```
  출고 처리 완료.
   주문번호   : ORD-...
   상태 변경  : CONFIRMED → [RELEASE]
  ```
- 출고 실패 메시지는 기존과 동일하게 `f"출고 실패: {error}"`를 `show_message`로 출력한다
  (변경 없음).

### 7. 모니터링 (`monitoring_view.py`)
- `show_menu()`: 시료 관리와 동일한 패턴으로 변경한다.
- `show_order_counts_by_status(counts)`: 각 상태를 `render_status_badge(status)`로 감싸
  `f"{render_status_badge(status)}: {counts[status]}건"` 형태로 한 줄씩 출력한다(상태 목록과
  집계 로직 자체는 변경하지 않는다).
- `show_sample_stock_status(stock_status_list)`: 비어 있으면 기존과 동일한 안내 문구 유지.
  그 외에는 `render_table(["시료 ID", "이름", "재고수량", "상태"], rows, aligns)`를 사용하되
  (`aligns = ["<", "<", ">", ">"]`, 기존 `STOCK_COLUMN_HEADER`의 정렬과 동일), `상태`
  컬럼 값은 `render_status_badge(item['status'])`로 감싼 값(`[여유]`/`[부족]`/`[고갈]`)을
  넣는다.

## 예외/경계 케이스 (테스트에 반드시 포함)
- `render_table`: 빈 `rows` 전달 시 헤더 줄만 반환되는지 확인. 데이터 값이 헤더보다 길 때
  컬럼 폭이 데이터 길이에 맞춰 늘어나는지 확인. `aligns`에 지정된 대로 좌/우 정렬이 실제로
  반영되는지 확인. `aligns`의 길이가 `headers`와 다르면 `ValueError`가 발생하는지 확인.
- `render_progress_bar`: `total`이 0일 때 0%의 빈 바를 반환하는지, `current == total`일 때
  100%(모두 채워진 바)를 반환하는지, `current == 0`일 때 0%를 반환하는지 확인.
- `render_status_badge`: 임의의 문자열을 대괄호로 정확히 감싸는지 확인.
- 각 view의 목록류 메서드(`show_samples`, `show_reserved_orders`, `show_waiting_jobs`,
  `show_confirmed_orders`, `show_sample_stock_status`)가 빈 리스트일 때 기존 안내 문구를
  그대로 출력하는지(capsys로 캡처해) 확인.
- 각 view의 신규 결과 메서드(`show_reservation_success`, `show_approval_result`(충분/부족
  두 가지 모두), `show_rejection_result`, `show_registration_success`,
  `show_progress_result`(완료/미완료 모두), `show_release_result`)가 기대한 문자열을
  출력하는지 capsys로 확인.
- 기존 controller 단위 테스트(`tests/test_sample_controller.py`,
  `tests/test_order_controller.py`, `tests/test_approval_controller.py`,
  `tests/test_production_controller.py`, `tests/test_release_controller.py`,
  `tests/test_monitoring_controller.py`, `tests/test_main_controller.py`)가 `FakeView`에
  새 메서드를 추가한 뒤에도 전부 통과하는지 확인(모델 호출 로직 자체가 바뀌지 않았음을
  보증하는 회귀 테스트로 유지).

## 범위 제외
- Plan-step8.md의 "범위 제외" 절(메인 메뉴 신규 집계 항목, 주문 접수 확인 Y/N 게이트,
  승인 전 생산량 미리보기, 재고 잔여율 바/생산 완료 예정 시각, ANSI 색상)을 그대로 따른다.
- model의 판단 로직, 저장 방식, 메서드 시그니처는 변경하지 않는다.
- controller의 model 호출 순서/분기 조건은 변경하지 않는다(문자열 조립 책임의 view 이관만
  허용).
