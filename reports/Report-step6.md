## Step 6 구현 리포트

### 구현 범위
- 주문량 확인: `MonitoringModel.count_orders_by_status()`가 `OrderModel.all()`을 조회해 RESERVED/CONFIRMED/PRODUCING/RELEASE 4개 상태별 건수를 딕셔너리로 집계한다. REJECTED 상태는 집계에서 제외하며, 주문이 없는 상태도 각 상태 0건으로 표시된다.
- 재고량 확인: `MonitoringModel.sample_stock_status()`가 `SampleModel.all()`로 전체 시료를 조회하고, 각 시료마다 `OrderModel.list_reserved()`에서 해당 sample_id와 일치하는 주문의 quantity 합(수요)을 계산해 재고 상태(고갈/여유/부족)를 판정한다. 판정 로직은 Plan/PRD의 설계 결정(재고 0이면 무조건 고갈, 그 외 재고>=수요면 여유, 재고<수요면 부족)을 그대로 따른다.
- 콘솔 뷰(`MonitoringView`)/컨트롤러(`MonitoringController`)를 통해 "1. 주문량 확인 / 2. 재고량 확인 / 3. 종료" 메뉴를 제공한다. 시료가 없으면 "등록된 시료가 없습니다." 안내를 출력한다.
- 새 저장소는 추가하지 않았으며, 기존 `SampleModel`/`OrderModel` 인스턴스를 주입받아 조회·집계만 수행하는 읽기 전용 구조로 구현했다(데이터 변경 메서드 없음).

### 생성/수정 파일 목록
- `model/monitoring_model.py` (신규): 상태별 주문 건수 집계, 시료별 재고 상태 판정을 담당하는 도메인 모델.
- `view/monitoring_view.py` (신규): 모니터링 메뉴, 주문 건수 출력, 시료별 재고 상태 표 출력 등 콘솔 입출력 담당.
- `controller/monitoring_controller.py` (신규): 모니터링 메뉴 선택 흐름 제어(1: 주문량 확인, 2: 재고량 확인, 3: 종료).
- `tests/test_monitoring_model.py` (신규): 모델 단위 테스트.
- `tests/test_monitoring_controller.py` (신규): 컨트롤러 흐름 테스트.

### 작성한 테스트
- `tests/test_monitoring_model.py`
  - 주문이 없을 때 4개 상태 모두 0건
  - REJECTED 주문이 집계에서 제외되는지 확인
  - 여러 상태(RESERVED/CONFIRMED/PRODUCING/RELEASE/REJECTED)가 혼재할 때 각 상태별 건수 정확성
  - 시료가 없을 때 재고 상태 결과가 빈 리스트
  - 재고 0인 시료는 RESERVED 주문이 있어도 "고갈"
  - 재고와 RESERVED 수요 합이 정확히 같은 경계값 → "여유"
  - 재고가 수요보다 1 적은 경우 → "부족"
  - RESERVED 주문이 없는 양의 재고 시료 → "여유"
  - 한 시료에 여러 RESERVED 주문이 있을 때 수량 합산으로 여유/부족 전환 확인
  - CONFIRMED/PRODUCING/REJECTED/RELEASE 주문 수량이 수요 계산에 포함되지 않는지 확인
- `tests/test_monitoring_controller.py`
  - 주문이 없을 때 주문량 확인 메뉴가 4개 상태 모두 0건으로 보고
  - 상태 혼재 시 주문량 확인 메뉴 결과가 정확히 반영되는지 확인
  - 시료가 없을 때 재고량 확인 메뉴가 빈 목록을 보고
  - 고갈/여유가 혼재하는 시료 목록에 대해 재고량 확인 메뉴가 시료별 상태를 정확히 보고
  - 잘못된 메뉴 선택 시 오류 메시지 출력

작업 완료 후 `pytest`를 실행해 신규 테스트 15건을 포함한 전체 147건이 모두 통과함을 확인했다.
