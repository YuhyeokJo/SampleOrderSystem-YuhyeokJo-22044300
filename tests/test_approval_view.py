from model.order import Order
from view.approval_view import ApprovalView


def test_show_reserved_orders_reports_empty_message_when_no_orders(capsys):
    view = ApprovalView()

    view.show_reserved_orders([])

    assert capsys.readouterr().out == "접수된(RESERVED) 주문이 없습니다.\n"


def test_show_reserved_orders_prints_count_and_numbered_table(capsys):
    view = ApprovalView()
    orders = [Order.create_reserved("ORD-1", "S-1", "Customer-A", 5)]

    view.show_reserved_orders(orders)

    lines = capsys.readouterr().out.splitlines()
    assert lines[0] == "접수된 주문 목록 (RESERVED, 총 1건)"
    assert lines[1].startswith("번호")
    assert lines[2].startswith("1")
    assert "ORD-1" in lines[2]


def test_show_approval_result_when_stock_sufficient(capsys):
    view = ApprovalView()
    order = Order.create_reserved("ORD-1", "S-1", "Customer-A", 5).with_status("CONFIRMED")

    view.show_approval_result(order, None)

    output = capsys.readouterr().out
    assert "승인 완료." in output
    assert " 주문번호   : ORD-1" in output
    assert " 상태 변경  : RESERVED → [CONFIRMED]" in output
    assert "부족분" not in output


def test_show_approval_result_when_stock_short(capsys):
    view = ApprovalView()
    order = Order.create_reserved("ORD-1", "S-1", "Customer-A", 101).with_status("PRODUCING")

    view.show_approval_result(order, 1)

    output = capsys.readouterr().out
    assert " 상태 변경  : RESERVED → [PRODUCING]" in output
    assert " 부족분     : 1 (생산라인에 등록되었습니다)" in output


def test_show_rejection_result_prints_status_transition(capsys):
    view = ApprovalView()
    order = Order.create_reserved("ORD-1", "S-1", "Customer-A", 5).with_status("REJECTED")

    view.show_rejection_result(order)

    output = capsys.readouterr().out
    assert "거절 완료." in output
    assert " 주문번호   : ORD-1" in output
    assert " 상태 변경  : RESERVED → [REJECTED]" in output
