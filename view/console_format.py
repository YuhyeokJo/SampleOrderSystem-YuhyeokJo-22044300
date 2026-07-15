"""콘솔 출력 포맷을 공통으로 렌더링하는 헬퍼 모듈."""


def render_divider(width=64):
    return "=" * width


def render_table(headers, rows, aligns):
    if len(aligns) != len(headers):
        raise ValueError("aligns의 길이는 headers와 같아야 합니다.")

    str_rows = [[str(value) for value in row] for row in rows]
    column_widths = []
    for index, header in enumerate(headers):
        cell_lengths = [len(row[index]) for row in str_rows]
        column_widths.append(max([len(header)] + cell_lengths) + 2)

    def render_row(values):
        cells = []
        for value, width, align in zip(values, column_widths, aligns):
            cells.append(f"{value:{align}{width}}")
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
