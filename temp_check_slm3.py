from common import get_sheet

ws = get_sheet().spreadsheet.worksheet("SLMLog")
rows = ws.get_all_values()
print("SON 3 SATIR (tarih, saat, TIP, mesaj):")
for r in rows[-3:]:
    print(r[:4])
