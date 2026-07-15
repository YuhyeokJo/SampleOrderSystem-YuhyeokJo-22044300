from model.order import Order
from view.order_view import OrderView


def test_show_input_summary_prints_entered_values(capsys):
    view = OrderView()

    view.show_input_summary("S-001", "삼성전자 파운드리", 200)

    output = capsys.readouterr().out
    assert "입력 내용 확인" in output
    assert " 시료 ID  : S-001" in output
    assert " 고객명   : 삼성전자 파운드리" in output
    assert " 주문 수량 : 200" in output


def test_show_reservation_success_prints_order_number_and_status_badge(capsys):
    view = OrderView()
    order = Order.create_reserved("ORD-20260416-0001", "S-001", "삼성전자 파운드리", 200)

    view.show_reservation_success(order)

    output = capsys.readouterr().out
    assert "예약 접수 완료." in output
    assert " 주문번호 : ORD-20260416-0001" in output
    assert " 상태     : [RESERVED]" in output
