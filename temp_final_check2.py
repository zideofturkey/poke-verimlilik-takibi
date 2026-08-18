from common import get_gorevler_sheet

ws = get_gorevler_sheet()
rows = ws.get_all_values()
print("BaharSpot travail de reelSeo satirlari:")
for i, r in enumerate(rows):
    if "baharspot travail de reelseo" in str(r).lower():
        print(f"satir {i+1}: {r}")
