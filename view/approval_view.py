from view.console_format import render_divider, render_status_badge, render_table


class ApprovalView:
    """주문 승인/거절 기능의 콘솔 입출력을 담당한다."""

    def show_menu(self):
        print(render_divider())
        print(" [3] 주문 승인/거절")
        print(render_divider())
        print(" [1] 접수된 주문 목록 조회  [2] 주문 승인  [3] 주문 거절  [4] 종료")

    def prompt_choice(self):
        return input("선택 > ").strip()

    def prompt_order_id(self):
        return input("주문번호: ").strip()

    def show_message(self, message):
        print(message)

    def show_reserved_orders(self, orders):
        if not orders:
            print("접수된(RESERVED) 주문이 없습니다.")
            return
        print(f"접수된 주문 목록 (RESERVED, 총 {len(orders)}건)")
        headers = ["번호", "주문번호", "시료 ID", "고객명", "주문수량", "상태"]
        rows = [
            [index, order.order_id, order.sample_id, order.customer_name, order.quantity, order.status]
            for index, order in enumerate(orders, start=1)
        ]
        for line in render_table(headers, rows, ["<", "<", "<", "<", ">", ">"]):
            print(line)

    def show_approval_result(self, order, shortage_quantity):
        print("승인 완료.")
        print(f" 주문번호   : {order.order_id}")
        print(f" 상태 변경  : RESERVED → {render_status_badge(order.status)}")
        if shortage_quantity is not None:
            print(f" 부족분     : {shortage_quantity} (생산라인에 등록되었습니다)")

    def show_rejection_result(self, order):
        print("거절 완료.")
        print(f" 주문번호   : {order.order_id}")
        print(f" 상태 변경  : RESERVED → {render_status_badge(order.status)}")
