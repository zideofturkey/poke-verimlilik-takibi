from common import get_sheet

ws = get_sheet().spreadsheet.worksheet("SLMLog")
rows = ws.get_all_values()
print("SON SATIR (TIP + mesaj):")
print(rows[-1][:4])
