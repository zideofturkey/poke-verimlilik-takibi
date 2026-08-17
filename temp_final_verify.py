from common import get_sheet, get_gorevler_sheet

ws = get_sheet().spreadsheet.worksheet("SLMLog")
rows = ws.get_all_values()
print("SON SATIR (TIP + mesaj):")
son = rows[-1]
print(son[:4])

ws2 = get_gorevler_sheet()
rows2 = ws2.get_all_values()
print("\nGunlukGorevler'de 'ulen' var mi kontrol:")
bulundu = False
for r in rows2:
    if any("ulen" in str(c).lower() for c in r):
        print("BULUNDU:", r)
        bulundu = True
if not bulundu:
    print("Kontaminasyon YOK - temiz.")
