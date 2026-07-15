from view.console_format import render_divider, render_status_badge


class OrderView:
    """시료 주문 접수 기능의 콘솔 입출력을 담당한다."""

    def show_menu(self):
        print(render_divider())
        print(" [2] 시료 주문")
        print(render_divider())
        print(" [1] 시료 주문 접수  [2] 종료")

    def prompt_choice(self):
        return input("선택 > ").strip()

    def prompt_sample_id(self):
        return input("시료 ID: ").strip()

    def prompt_customer_name(self):
        return input("고객명: ").strip()

    def prompt_quantity(self):
        return input("주문 수량: ").strip()

    def show_message(self, message):
        print(message)

    def show_input_summary(self, sample_id, customer_name, quantity):
        print("입력 내용 확인")
        print(f" 시료 ID  : {sample_id}")
        print(f" 고객명   : {customer_name}")
        print(f" 주문 수량 : {quantity}")

    def show_reservation_success(self, order):
        print("예약 접수 완료.")
        print(f" 주문번호 : {order.order_id}")
        print(f" 상태     : {render_status_badge(order.status)}")
