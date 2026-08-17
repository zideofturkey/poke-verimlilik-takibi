from common import get_gorevler_sheet

ws = get_gorevler_sheet()
rows = ws.get_all_values()
print("'ulen' iceren satirlar:")
for i, r in enumerate(rows):
    if any("ulen" in str(c).lower() for c in r):
        print(f"satir {i+1}: {r}")
