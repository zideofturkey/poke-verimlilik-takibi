from common import get_gorevler_sheet

ws = get_gorevler_sheet()
rows = ws.get_all_values()
print("Yucuf/BaharSpot iceren TUM satirlar:")
for i, r in enumerate(rows):
    if any("yucuf" in str(c).lower() or "baharspot" in str(c).lower() for c in r):
        print(f"satir {i+1}: {r}")
