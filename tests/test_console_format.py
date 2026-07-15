import pytest

from view.console_format import (
    render_divider,
    render_progress_bar,
    render_status_badge,
    render_table,
)


def test_render_divider_default_width():
    assert render_divider() == "=" * 64


def test_render_divider_custom_width():
    assert render_divider(10) == "=" * 10


def test_render_table_returns_header_only_when_rows_empty():
    lines = render_table(["A", "B"], [], ["<", ">"])
    assert lines == [f"{'A':<3}{'B':>3}"]


def test_render_table_aligns_left_and_right():
    lines = render_table(["이름", "수량"], [["Wafer-A", 5]], ["<", ">"])
    assert lines[0] == f"{'이름':<9}{'수량':>4}"
    assert lines[1] == f"{'Wafer-A':<9}{5:>4}"


def test_render_table_column_width_grows_with_data_length():
    lines = render_table(["ID"], [["VERY-LONG-ID"]], ["<"])
    expected_width = len("VERY-LONG-ID") + 2
    assert lines[0] == f"{'ID':<{expected_width}}"
    assert lines[1] == f"{'VERY-LONG-ID':<{expected_width}}"


def test_render_table_raises_value_error_when_aligns_length_mismatches_headers():
    with pytest.raises(ValueError):
        render_table(["A", "B"], [["1", "2"]], ["<"])


def test_render_status_badge_wraps_status_in_brackets():
    assert render_status_badge("RESERVED") == "[RESERVED]"


def test_render_progress_bar_returns_empty_bar_when_total_is_zero():
    assert render_progress_bar(0, 0) == f"[{'░' * 20}] 0%"


def test_render_progress_bar_returns_zero_percent_when_current_is_zero():
    assert render_progress_bar(0, 10) == f"[{'░' * 20}] 0%"


def test_render_progress_bar_returns_fully_filled_bar_when_current_equals_total():
    assert render_progress_bar(10, 10) == f"[{'█' * 20}] 100%"


def test_render_progress_bar_returns_partial_bar_for_intermediate_ratio():
    assert render_progress_bar(124, 206, width=20) == "[████████████░░░░░░░░] 60%"
