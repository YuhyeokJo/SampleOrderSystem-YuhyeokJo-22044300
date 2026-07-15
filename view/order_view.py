class OrderView:
    """시료 주문 접수 기능의 콘솔 입출력을 담당한다."""

    MENU = """
==== 시료 주문 접수 ====
1. 시료 주문 접수
2. 종료
"""

    def show_menu(self):
        print(self.MENU)

    def prompt_choice(self):
        return input("메뉴를 선택하세요: ").strip()

    def prompt_sample_id(self):
        return input("시료 ID: ").strip()

    def prompt_customer_name(self):
        return input("고객명: ").strip()

    def prompt_quantity(self):
        return input("주문 수량: ").strip()

    def show_message(self, message):
        print(message)
