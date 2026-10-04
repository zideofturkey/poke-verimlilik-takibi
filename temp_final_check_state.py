from common import get_haftalik_sheet, get_haftalik_rutin_takip_sheet, hafta_baslangic_str

hafta = hafta_baslangic_str()
print("Bu hafta:", hafta)

ws1 = get_haftalik_sheet()
print("\nHaftalikHedefler:")
for r in ws1.get_all_records():
    if r.get("HaftaBaslangic") == hafta:
        print(" ", r)

ws2 = get_haftalik_rutin_takip_sheet()
print("\nHaftalikRutinTakip:")
for row in ws2.get_all_values()[1:]:
    if row and row[0] == hafta:
        print(" ", row)
