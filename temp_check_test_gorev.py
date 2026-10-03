from common import get_gorevler_sheet

ws = get_gorevler_sheet()
rows = ws.get_all_values()
for i, r in enumerate(rows):
    if "Claude test gorevi silme ornegi" in str(r):
        print(f"satir {i+1}: {r}")
