from view.console_format import render_divider, render_status_badge, render_table


class ReleaseView:
    """출고 처리 기능의 콘솔 입출력을 담당한다."""

    def show_menu(self):
        print(render_divider())
        print(" [6] 출고 처리")
        print(render_divider())
        print(" [1] 승인 완료(CONFIRMED) 주문 목록 조회  [2] 출고 처리  [3] 종료")

    def prompt_choice(self):
        return input("선택 > ").strip()

    def prompt_order_id(self):
        return input("주문번호: ").strip()

    def show_message(self, message):
        print(message)

    def show_confirmed_orders(self, orders):
        if not orders:
            print("승인 완료(CONFIRMED)된 주문이 없습니다.")
            return
        print(f"승인 완료(CONFIRMED) 주문 목록 (총 {len(orders)}건)")
        headers = ["번호", "주문번호", "시료 ID", "고객명", "주문수량", "상태"]
        rows = [
            [index, order.order_id, order.sample_id, order.customer_name, order.quantity, order.status]
            for index, order in enumerate(orders, start=1)
        ]
        for line in render_table(headers, rows, ["<", "<", "<", "<", ">", ">"]):
            print(line)

    def show_release_result(self, order):
        print("출고 처리 완료.")
        print(f" 주문번호   : {order.order_id}")
        print(f" 상태 변경  : CONFIRMED → {render_status_badge(order.status)}")
