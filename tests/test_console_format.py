import unicodedata

import pytest

from view.console_format import (
    render_divider,
    render_progress_bar,
    render_status_badge,
    render_table,
)


def _display_width(text):
    """한글 등 전각 문자를 2칸으로 세는 독립적인 표시 폭 계산(테스트용 오라클)."""
    return sum(2 if unicodedata.east_asian_width(char) in ("W", "F") else 1 for char in text)


def _padded(text, width, align):
    padding = " " * max(0, width - _display_width(text))
    return padding + text if align == ">" else text + padding


def test_render_divider_default_width():
    assert render_divider() == "=" * 64


def test_render_divider_custom_width():
    assert render_divider(10) == "=" * 10


def test_render_table_returns_header_only_when_rows_empty():
    lines = render_table(["A", "B"], [], ["<", ">"])
    assert lines == [f"{'A':<3}{'B':>3}"]


def test_render_table_aligns_left_and_right():
    lines = render_table(["이름", "수량"], [["Wafer-A", 5]], ["<", ">"])
    col0_width = max(_display_width("이름"), _display_width("Wafer-A")) + 2
    col1_width = max(_display_width("수량"), _display_width("5")) + 2
    assert lines[0] == _padded("이름", col0_width, "<") + _padded("수량", col1_width, ">")
    assert lines[1] == _padded("Wafer-A", col0_width, "<") + _padded("5", col1_width, ">")


def test_render_table_korean_and_ascii_columns_share_equal_display_width():
    """한글 헤더/영문 데이터가 섞여도 모든 줄의 화면상 표시 폭이 동일해야 한다(정렬 회귀 테스트)."""
    lines = render_table(
        ["시료 ID", "이름", "평균 생산시간", "수율", "현재 재고"],
        [["S-001", "Wafer", 1.0, 0.9, 100]],
        ["<", "<", ">", ">", ">"],
    )
    widths = {_display_width(line) for line in lines}
    assert len(widths) == 1


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
