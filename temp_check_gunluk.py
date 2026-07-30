from common import get_gorevler_sheet

ws = get_gorevler_sheet()
rows = ws.get_all_values()
print("SON 8 SATIR:")
for r in rows[-8:]:
    print(r)
