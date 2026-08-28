from common import get_durum_sheet

ws = get_durum_sheet()
rows = ws.get_all_values()
for i, r in enumerate(rows):
    if r and r[0] == "test_anahtar_gecici":
        print(f"Siliniyor: satir {i+1} -> {r}")
        ws.delete_rows(i + 1)
        break
else:
    print("Bulunamadi")
