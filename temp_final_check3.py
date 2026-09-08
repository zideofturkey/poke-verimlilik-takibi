from common import get_sheet, get_gorevler_sheet

ws = get_sheet().spreadsheet.worksheet("SLMLog")
rows = ws.get_all_values()
print("SON SATIR:")
print(rows[-1][:4])

print("\nGunlukGorevler'de 'Dünden kalan' kontrolu:")
ws2 = get_gorevler_sheet()
rows2 = ws2.get_all_values()
bulundu = False
for r in rows2:
    if any("dünden kalan" in str(c).lower() for c in r):
        print("BULUNDU (kontaminasyon var):", r)
        bulundu = True
if not bulundu:
    print("Kontaminasyon YOK - temiz.")
