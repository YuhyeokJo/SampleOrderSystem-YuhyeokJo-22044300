from view.console_format import render_divider, render_table


class SampleView:
    """시료 관리 기능의 콘솔 입출력을 담당한다."""

    def show_menu(self):
        print(render_divider())
        print(" [1] 시료 관리")
        print(render_divider())
        print(" [1] 시료 등록  [2] 시료 목록 조회  [3] 시료 검색  [4] 종료")

    def prompt_choice(self):
        return input("선택 > ").strip()

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
        print(f"등록 시료 목록 (총 {len(samples)}종)")
        headers = ["시료 ID", "이름", "평균 생산시간", "수율", "현재 재고"]
        rows = [
            [sample.sample_id, sample.name, sample.avg_production_time, sample.yield_rate, sample.stock_quantity]
            for sample in samples
        ]
        for line in render_table(headers, rows, ["<", "<", ">", ">", ">"]):
            print(line)
