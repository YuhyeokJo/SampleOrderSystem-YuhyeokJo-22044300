class SampleView:
    """시료 관리 기능의 콘솔 입출력을 담당한다."""

    MENU = """
==== 시료 관리 ====
1. 시료 등록
2. 시료 목록 조회
3. 시료 검색
4. 종료
"""

    COLUMN_HEADER = f"{'시료 ID':<12}{'이름':<16}{'평균 생산시간':>14}{'수율':>8}{'재고 수량':>10}"

    def show_menu(self):
        print(self.MENU)

    def prompt_choice(self):
        return input("메뉴를 선택하세요: ").strip()

    def prompt_sample_id(self):
        return input("시료 ID: ").strip()

    def prompt_name(self):
        return input("이름: ").strip()

    def prompt_avg_production_time(self):
        return input("평균 생산시간(min/ea): ").strip()

    def prompt_yield_rate(self):
        return input("수율(0.0~1.0): ").strip()

    def prompt_stock_quantity(self):
        return input("초기 재고 수량: ").strip()

    def prompt_search_keyword(self):
        return input("검색할 이름을 입력하세요: ").strip()

    def show_message(self, message):
        print(message)

    def show_samples(self, samples):
        if not samples:
            print("등록된 시료가 없습니다.")
            return
        print(self.COLUMN_HEADER)
        for sample in samples:
            print(
                f"{sample.sample_id:<12}{sample.name:<16}"
                f"{sample.avg_production_time:>14}{sample.yield_rate:>8}{sample.stock_quantity:>10}"
            )
