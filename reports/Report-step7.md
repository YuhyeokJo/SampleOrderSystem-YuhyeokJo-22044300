## Step 7 구현 리포트

### 구현 범위
- **MainController.run()**: while 루프에서 매 반복마다 새 `SampleModel()`을 생성해 `all()`을 조회하고, 시료 종류 수와 재고 수량 합계를 계산해 view에 전달(캐시 없이 매번 재조회). 요약 정보와 메뉴(1~7)를 표시한 뒤 입력을 받아 1~6은 대응 컨트롤러의 `run()` 호출 후 루프 재시작, 7은 종료 메시지 출력 후 루프 종료, 그 외(범위 밖 숫자·비숫자)는 오류 안내 후 메뉴 재표시.
- 시료가 없을 때는 "등록된 시료가 없습니다."만 표시(재고 합계 미표시), 요약 계산 로직은 `MainController._show_summary`에 위치.
- 하위 컨트롤러 검증을 위해 생성자에서 `controllers` 딕셔너리(예: `{"1": SampleController(), ...}`)를 주입받을 수 있도록 설계. 기본값은 `_default_controllers()`가 반환하는 실제 6개 컨트롤러(SampleController/OrderController/ApprovalController/MonitoringController/ProductionController/ReleaseController).
- **MainMenuView**: 요약 정보 표시(`show_summary`), 메뉴 표시(`show_menu`), 입력 수신(`prompt_choice`), 메시지 출력(`show_message`) 등 콘솔 입출력 전담.
- **main.py**: 기존 `SampleController().run()`을 `MainController().run()`으로 교체.
- Step 1~6의 기존 컨트롤러/모델/뷰 코드는 전혀 수정하지 않고 그대로 재사용.

### 생성/수정 파일 목록
- `controller/main_controller.py` (신규): 메인 메뉴 라우팅 및 요약 정보 재조회 로직.
- `view/main_menu_view.py` (신규): 메인 메뉴 콘솔 입출력.
- `main.py` (수정): 진입점을 `MainController`로 교체.
- `tests/test_main_controller.py` (신규): MainController 단위 테스트.

### 작성한 테스트
`tests/test_main_controller.py`:
- `test_summary_shows_no_samples_message_when_empty`: 시료가 없을 때 요약 정보가 (0, 0)으로 전달되어 "등록된 시료가 없습니다." 처리 경로를 타는지 확인.
- `test_summary_reports_sample_count_and_total_stock`: 시료 2개 등록 시 종류 수 2, 재고 합계 128이 정확히 계산되는지 확인.
- `test_each_menu_choice_invokes_matching_controller`: 1~6번 선택 시 각각 대응하는(주입된) 가짜 컨트롤러의 `run()`이 정확히 1회씩 호출되는지 확인.
- `test_exit_choice_ends_main_menu_loop`: 7번 선택 시 종료 메시지가 출력되고 루프가 즉시 종료(메뉴 1회만 표시)되는지 확인.
- `test_invalid_choice_shows_error_and_reshows_menu`: 0, 8, "abc" 입력 시 매번 오류 안내가 출력되고 메뉴가 재표시(총 4회)되는지 확인.
- `test_returns_to_main_menu_after_sub_controller_finishes`: 하위 컨트롤러 실행 후 메인 메뉴로 복귀해 메뉴가 다시 표시되는지 확인.
- `test_summary_refreshes_after_sample_registered_via_real_sample_controller`: 실제 `SampleModel`/`SampleController`/`SampleView`를 사용해 1번 메뉴에서 새 시료를 등록한 뒤 메인 메뉴로 복귀했을 때, 요약 정보가 (0, 0) -> (1, 50)으로 캐시 없이 갱신되는지 확인.

전체 테스트: `python -m pytest -q` 실행 결과 154개 전체 통과.
