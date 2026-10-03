from common import get_gorevler_sheet, get_cop_kutusu_sheet

ws1 = get_gorevler_sheet()
rows1 = ws1.get_all_values()
bulundu = False
for r in rows1:
    if "Claude cop kutusu test gorevi" in str(r):
        print(f"HALA GunlukGorevler'de VAR: {r}")
        bulundu = True
if not bulundu:
    print("GunlukGorevler'den SILINMIS - basarili.")

ws2 = get_cop_kutusu_sheet()
rows2 = ws2.get_all_values()
print("\nCopKutusu TUM satirlar:")
for r in rows2:
    print(r)
