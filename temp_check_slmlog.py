from common import get_sheet

ws = get_sheet().spreadsheet.worksheet("SLMLog")
rows = ws.get_all_values()
print("SON 3 SATIR:")
for r in rows[-3:]:
    print(r)
