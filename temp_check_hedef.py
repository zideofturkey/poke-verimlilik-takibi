from common import get_haftalik_sheet, hafta_baslangic_str

ws = get_haftalik_sheet()
rows = ws.get_all_records()
hafta = hafta_baslangic_str()
print("HAFTA_BASI:", hafta)
bulundu = False
for r in rows:
    if r.get("HaftaBaslangic") == hafta:
        bulundu = True
        print("KAYIT:", r)
if not bulundu:
    print("BU_HAFTA_ICIN_KAYIT_YOK")
