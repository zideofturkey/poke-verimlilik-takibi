from common import get_gorevler_sheet

ws = get_gorevler_sheet()
rows = ws.get_all_values()
print("'geçen haftaki' iceren satirlar (kontaminasyon kontrolu):")
bulundu = False
for r in rows:
    if any("geçen haftaki" in str(c).lower() for c in r):
        print("BULUNDU:", r)
        bulundu = True
if not bulundu:
    print("Kontaminasyon YOK - temiz.")
