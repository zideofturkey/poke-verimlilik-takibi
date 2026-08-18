from common import get_gorevler_sheet

ws = get_gorevler_sheet()
rows = ws.get_all_values()
print("Yucuf iceren satirlar:")
for i, r in enumerate(rows):
    if "yucuf" in str(r).lower():
        print(f"satir {i+1}: {r}")
