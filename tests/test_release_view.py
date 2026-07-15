from model.order import Order
from view.release_view import ReleaseView


def test_show_confirmed_orders_reports_empty_message_when_no_orders(capsys):
    view = ReleaseView()

    view.show_confirmed_orders([])

    assert capsys.readouterr().out == "승인 완료(CONFIRMED)된 주문이 없습니다.\n"


def test_show_confirmed_orders_prints_count_and_numbered_table(capsys):
    view = ReleaseView()
    orders = [Order.create_reserved("ORD-1", "S-1", "Customer-A", 5).with_status("CONFIRMED")]

    view.show_confirmed_orders(orders)

    lines = capsys.readouterr().out.splitlines()
    assert lines[0].startswith("승인 완료(CONFIRMED) 주문 목록 (총 1건)")
    assert lines[1].startswith("번호")
    assert lines[2].startswith("1")
    assert "ORD-1" in lines[2]


def test_show_release_result_prints_status_transition(capsys):
    view = ReleaseView()
    order = Order.create_reserved("ORD-1", "S-1", "Customer-A", 5).with_status("RELEASE")

    view.show_release_result(order)

    output = capsys.readouterr().out
    assert "출고 처리 완료." in output
    assert " 주문번호   : ORD-1" in output
    assert " 상태 변경  : CONFIRMED → [RELEASE]" in output
