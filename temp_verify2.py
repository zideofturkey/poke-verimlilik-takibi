from common import get_haftalik_sheet, hafta_baslangic_str, get_gorevler_sheet

ws = get_haftalik_sheet()
hafta = hafta_baslangic_str()
rows = ws.get_all_values()
print("--- HaftalikHedefler (bu hafta) ---")
for r in rows:
    if r and r[0] == hafta:
        print(r)

ws2 = get_gorevler_sheet()
rows2 = ws2.get_all_values()
print("--- GunlukGorevler (son 3 satir - kontaminasyon var mi) ---")
for r in rows2[-3:]:
    print(r)
