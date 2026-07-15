from view.console_format import render_divider, render_progress_bar, render_table


class ProductionView:
    """생산라인 관리 기능의 콘솔 입출력을 담당한다."""

    def show_menu(self):
        print(render_divider())
        print(" [5] 생산라인")
        print(render_divider())
        print(" [1] 생산 큐 등록  [2] 생산 진행 기록  [3] 생산 현황 조회  [4] 대기 주문 확인  [5] 종료")

    def prompt_choice(self):
        return input("선택 > ").strip()

    def prompt_order_id(self):
        return input("주문번호: ").strip()

    def prompt_sample_id(self):
        return input("시료 ID: ").strip()

    def prompt_shortage_quantity(self):
        return input("부족분: ").strip()

    def prompt_produced_quantity(self):
        return input("이번에 생산된 수량: ").strip()

    def show_message(self, message):
        print(message)

    def show_current_job(self, job):
        if job is None:
            print("진행 중인 생산 항목이 없습니다.")
            return
        print("현재 생산 중")
        print(f" 주문번호    : {job.order_id}")
        print(f" 시료 ID     : {job.sample_id}")
        print(f" 부족분      : {job.shortage_quantity}")
        print(f" 실 생산량   : {job.actual_production_quantity}      총 생산 시간 : {job.total_production_time}")
        progress_bar = render_progress_bar(job.produced_quantity, job.actual_production_quantity)
        print(f" 진행률      : {progress_bar} ({job.produced_quantity}/{job.actual_production_quantity})")

    def show_waiting_jobs(self, jobs):
        if not jobs:
            print("대기 중인 생산 항목이 없습니다.")
            return
        print(f"대기 중인 생산 항목 (총 {len(jobs)}건, FIFO)")
        headers = ["순번", "주문번호", "시료 ID", "부족분", "실 생산량", "총 생산 시간"]
        rows = [
            [index, job.order_id, job.sample_id, job.shortage_quantity, job.actual_production_quantity, job.total_production_time]
            for index, job in enumerate(jobs, start=1)
        ]
        for line in render_table(headers, rows, ["<", "<", "<", ">", ">", ">"]):
            print(line)

    def show_registration_success(self, job):
        print(
            f"생산 큐 등록 완료. 실 생산량: {job.actual_production_quantity}, "
            f"총 생산 시간: {job.total_production_time}"
        )

    def show_progress_result(self, job, completed):
        if completed:
            print(f"생산 완료: 주문번호 {job.order_id}, 상태 변경: PRODUCING → [CONFIRMED]")
            return
        progress_bar = render_progress_bar(job.produced_quantity, job.actual_production_quantity)
        print(f"진행 기록 완료: {progress_bar} ({job.produced_quantity}/{job.actual_production_quantity})")
