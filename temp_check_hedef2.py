from common import get_haftalik_sheet, hafta_baslangic_str

ws = get_haftalik_sheet()
rows = ws.get_all_records()
hafta = hafta_baslangic_str()
print("HAFTA_BASI (bugunu iceren hafta):", hafta)
print("--- TUM SATIRLAR ---")
for r in rows:
    print(r)
