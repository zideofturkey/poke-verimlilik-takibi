from common import get_haftalik_sheet, hafta_baslangic_str

ws = get_haftalik_sheet()
rows = ws.get_all_values()
hafta = hafta_baslangic_str()
print("HAFTA_BASI:", hafta)
for r in rows:
    if r and r[0] == hafta:
        print(r)
