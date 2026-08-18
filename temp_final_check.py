from common import get_sheet, get_gorevler_sheet

ws = get_sheet().spreadsheet.worksheet("SLMLog")
rows = ws.get_all_values()
print("SON SATIR (TIP + mesaj):")
print(rows[-1][:4])

print("\nGunlukGorevler'de BaharSpot travail de reelSeo satirlari:")
ws2 = get_gorevler_sheet()
rows2 = ws2.get_all_values()
for i, r in enumerate(rows2):
    if "baharspot travail de reelseo" in str(r).lower():
        print(f"satir {i+1}: {r}")
