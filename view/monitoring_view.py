from model.monitoring_model import MONITORED_ORDER_STATUSES
from view.console_format import render_divider, render_status_badge, render_table


class MonitoringView:
    """모니터링 기능의 콘솔 입출력을 담당한다."""

    def show_menu(self):
        print(render_divider())
        print(" [4] 모니터링")
        print(render_divider())
        print(" [1] 주문량 확인  [2] 재고량 확인  [3] 종료")

    def prompt_choice(self):
        return input("선택 > ").strip()

    def show_message(self, message):
        print(message)

    def show_order_counts_by_status(self, counts):
        for status in MONITORED_ORDER_STATUSES:
            print(f"{render_status_badge(status)}: {counts[status]}건")

    def show_sample_stock_status(self, stock_status_list):
        if not stock_status_list:
            print("등록된 시료가 없습니다.")
            return
        headers = ["시료 ID", "이름", "재고수량", "상태"]
        rows = [
            [item["sample_id"], item["name"], item["stock_quantity"], render_status_badge(item["status"])]
            for item in stock_status_list
        ]
        for line in render_table(headers, rows, ["<", "<", ">", ">"]):
            print(line)
