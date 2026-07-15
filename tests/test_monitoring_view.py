from view.monitoring_view import MonitoringView


def test_show_order_counts_by_status_prints_badges(capsys):
    view = MonitoringView()
    counts = {"RESERVED": 1, "CONFIRMED": 2, "PRODUCING": 0, "RELEASE": 0}

    view.show_order_counts_by_status(counts)

    output = capsys.readouterr().out
    assert "[RESERVED]: 1건" in output
    assert "[CONFIRMED]: 2건" in output
    assert "[PRODUCING]: 0건" in output
    assert "[RELEASE]: 0건" in output


def test_show_sample_stock_status_reports_empty_message_when_no_samples(capsys):
    view = MonitoringView()

    view.show_sample_stock_status([])

    assert capsys.readouterr().out == "등록된 시료가 없습니다.\n"


def test_show_sample_stock_status_prints_table_with_status_badges(capsys):
    view = MonitoringView()
    stock_status_list = [
        {"sample_id": "S-1", "name": "Wafer-A", "stock_quantity": 0, "status": "고갈"},
        {"sample_id": "S-2", "name": "Wafer-B", "stock_quantity": 10, "status": "여유"},
    ]

    view.show_sample_stock_status(stock_status_list)

    lines = capsys.readouterr().out.splitlines()
    assert lines[0].startswith("시료 ID")
    assert "[고갈]" in lines[1]
    assert "[여유]" in lines[2]
