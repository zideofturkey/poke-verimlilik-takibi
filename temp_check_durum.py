from common import get_durum_sheet

ws = get_durum_sheet()
rows = ws.get_all_values()
print("TUM DURUM SATIRLARI:")
for r in rows:
    print(r)
