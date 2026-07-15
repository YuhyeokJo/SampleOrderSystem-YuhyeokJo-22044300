from model.monitoring_model import MONITORED_ORDER_STATUSES


class MonitoringView:
    """모니터링 기능의 콘솔 입출력을 담당한다."""

    MENU = """
==== 모니터링 ====
1. 주문량 확인
2. 재고량 확인
3. 종료
"""

    STOCK_COLUMN_HEADER = f"{'시료 ID':<12}{'이름':<16}{'재고수량':>8}{'상태':>8}"

    def show_menu(self):
        print(self.MENU)

    def prompt_choice(self):
        return input("메뉴를 선택하세요: ").strip()

    def show_message(self, message):
        print(message)

    def show_order_counts_by_status(self, counts):
        for status in MONITORED_ORDER_STATUSES:
            print(f"{status}: {counts[status]}건")

    def show_sample_stock_status(self, stock_status_list):
        if not stock_status_list:
            print("등록된 시료가 없습니다.")
            return
        print(self.STOCK_COLUMN_HEADER)
        for item in stock_status_list:
            print(
                f"{item['sample_id']:<12}{item['name']:<16}"
                f"{item['stock_quantity']:>8}{item['status']:>8}"
            )
