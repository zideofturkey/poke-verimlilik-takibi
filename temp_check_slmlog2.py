from common import get_sheet

ws = get_sheet().spreadsheet.worksheet("SLMLog")
rows = ws.get_all_values()
print("SON 2 SATIR:")
for r in rows[-2:]:
    print(r[:4])  # tarih, saat, tip, mesaj - prompt'u atla
