class ProductionView:
    """생산라인 관리 기능의 콘솔 입출력을 담당한다."""

    MENU = """
==== 생산라인 관리 ====
1. 생산 큐 등록
2. 생산 진행 기록
3. 생산 현황 조회
4. 대기 주문 확인
5. 종료
"""

    COLUMN_HEADER = f"{'주문번호':<20}{'시료 ID':<12}{'부족분':>8}{'실 생산량':>10}{'총 생산 시간':>14}"

    def show_menu(self):
        print(self.MENU)

    def prompt_choice(self):
        return input("메뉴를 선택하세요: ").strip()

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
        print(
            f"주문번호: {job.order_id}, 시료 ID: {job.sample_id}, 부족분: {job.shortage_quantity}, "
            f"실 생산량: {job.actual_production_quantity}, 총 생산 시간: {job.total_production_time}, "
            f"누적 생산량: {job.produced_quantity}"
        )

    def show_waiting_jobs(self, jobs):
        if not jobs:
            print("대기 중인 생산 항목이 없습니다.")
            return
        print(self.COLUMN_HEADER)
        for job in jobs:
            print(
                f"{job.order_id:<20}{job.sample_id:<12}{job.shortage_quantity:>8}"
                f"{job.actual_production_quantity:>10}{job.total_production_time:>14}"
            )
