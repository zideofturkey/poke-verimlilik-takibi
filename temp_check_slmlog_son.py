from common import get_sheet

ws = get_sheet().spreadsheet.worksheet("SLMLog")
rows = ws.get_all_values()
print("SON 15 SATIR (tarih, saat, tip, mesaj):")
for r in rows[-15:]:
    print(r[:4])
