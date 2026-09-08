from common import get_gorevler_sheet

ws = get_gorevler_sheet()
rows = ws.get_all_values()
print("'Dünden kalan' iceren satirlar:")
for i, r in enumerate(rows):
    if any("dünden kalan" in str(c).lower() for c in r):
        print(f"satir {i+1}: {r}")
