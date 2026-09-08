from common import get_haftalik_rutin_takip_sheet, hafta_baslangic_str, get_sheet

hafta = hafta_baslangic_str()
print("Bu hafta:", hafta)

ws = get_haftalik_rutin_takip_sheet()
rows = ws.get_all_values()
print("Bu hafta icin satirlar:")
for r in rows[1:]:
    if r and r[0] == hafta:
        print(r)

ws2 = get_sheet().spreadsheet.worksheet("SLMLog")
rows2 = ws2.get_all_values()
print("\nSON SATIR (siniflandirma):")
print(rows2[-1][:4])
