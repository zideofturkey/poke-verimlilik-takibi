from common import get_sheet

ws = get_sheet().spreadsheet.worksheet("HataLog")
rows = ws.get_all_values()
print("SON 15 HATA:")
for r in rows[-15:]:
    print(r)
