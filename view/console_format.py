"""콘솔 출력 포맷을 공통으로 렌더링하는 헬퍼 모듈."""

import unicodedata

_WIDE_EAST_ASIAN_WIDTHS = ("W", "F")


def render_divider(width=64):
    return "=" * width


def _display_width(text):
    """터미널에서 2칸을 차지하는 한글 등 전각 문자를 고려한 표시 폭을 계산한다."""
    return sum(2 if unicodedata.east_asian_width(char) in _WIDE_EAST_ASIAN_WIDTHS else 1 for char in text)


def _pad(value, width, align):
    padding = " " * max(0, width - _display_width(value))
    return padding + value if align == ">" else value + padding


def render_table(headers, rows, aligns):
    if len(aligns) != len(headers):
        raise ValueError("aligns의 길이는 headers와 같아야 합니다.")

    str_rows = [[str(value) for value in row] for row in rows]
    column_widths = []
    for index, header in enumerate(headers):
        cell_widths = [_display_width(row[index]) for row in str_rows]
        column_widths.append(max([_display_width(header)] + cell_widths) + 2)

    def render_row(values):
        cells = [
            _pad(value, width, align)
            for value, width, align in zip(values, column_widths, aligns)
        ]
        return "".join(cells)

    lines = [render_row(headers)]
    for row in str_rows:
        lines.append(render_row(row))
    return lines


def render_status_badge(status):
    return f"[{status}]"


def render_progress_bar(current, total, width=20):
    if total <= 0:
        return f"[{'░' * width}] 0%"

    filled = round(width * current / total)
    filled = max(0, min(width, filled))
    percent = round(current / total * 100)
    return f"[{'█' * filled}{'░' * (width - filled)}] {percent}%"
