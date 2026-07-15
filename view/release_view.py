class ReleaseView:
    """출고 처리 기능의 콘솔 입출력을 담당한다."""

    MENU = """
==== 출고 처리 ====
1. 승인 완료(CONFIRMED) 주문 목록 조회
2. 출고 처리
3. 종료
"""

    COLUMN_HEADER = f"{'주문번호':<20}{'시료 ID':<12}{'고객명':<12}{'주문수량':>8}{'상태':>10}"

    def show_menu(self):
        print(self.MENU)

    def prompt_choice(self):
        return input("메뉴를 선택하세요: ").strip()

    def prompt_order_id(self):
        return input("주문번호: ").strip()

    def show_message(self, message):
        print(message)

    def show_confirmed_orders(self, orders):
        if not orders:
            print("승인 완료(CONFIRMED)된 주문이 없습니다.")
            return
        print(self.COLUMN_HEADER)
        for order in orders:
            print(
                f"{order.order_id:<20}{order.sample_id:<12}{order.customer_name:<12}"
                f"{order.quantity:>8}{order.status:>10}"
            )
