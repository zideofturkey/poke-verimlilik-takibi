import os
from common import get_haftalik_sheet

ws = get_haftalik_sheet()
sh = ws.spreadsheet
print("SPREADSHEET_ID (koddaki):", sh.id)
print("SPREADSHEET_TITLE:", sh.title)
print("SHEET_ID env degeri:", os.environ.get("SHEET_ID"))
print("--- worksheet basliklari ---")
for w in sh.worksheets():
    print(w.title, w.row_count, w.col_count)
