from datetime import date
from pathlib import Path

import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter


COLUMNS = ["query_date", "timestamp", "account", "link", "tag", "content"]
HEADERS = {
    "query_date": "查詢日期",
    "timestamp": "發文時間",
    "account": "帳號",
    "link": "貼文連結",
    "tag": "標籤",
    "content": "內容",
}
COL_WIDTHS = {
    "query_date": 14,
    "timestamp": 24,
    "account": 20,
    "link": 50,
    "tag": 30,
    "content": 60,
}


def export(posts: list[dict], output_path: str) -> Path:
    """將貼文列表匯出為 Excel，回傳輸出路徑。"""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Threads 貼文"

    query_date = date.today().isoformat()

    # 標題行樣式
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="4A4A4A", end_color="4A4A4A", fill_type="solid")
    header_alignment = Alignment(horizontal="center", vertical="center")

    for col_idx, col_key in enumerate(COLUMNS, start=1):
        cell = ws.cell(row=1, column=col_idx, value=HEADERS[col_key])
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
        ws.column_dimensions[get_column_letter(col_idx)].width = COL_WIDTHS[col_key]

    ws.row_dimensions[1].height = 22

    # 資料行
    wrap = Alignment(wrap_text=True, vertical="top")
    for row_idx, post in enumerate(posts, start=2):
        row_data = [
            query_date,
            post.get("timestamp", ""),
            post.get("account", ""),
            post.get("link", ""),
            post.get("tag", ""),
            post.get("content", ""),
        ]
        for col_idx, value in enumerate(row_data, start=1):
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.alignment = wrap

    # 凍結標題行
    ws.freeze_panes = "A2"

    wb.save(str(output))
    return output
