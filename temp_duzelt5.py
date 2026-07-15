from common import get_sheet
ws = get_sheet()
rows = ws.get_all_values()
for i, row in enumerate(rows[1:], start=2):
    if len(row) >= 3 and row[0] == "2026-07-16" and "15 temmuz günü ortalama" in row[2]:
        ws.update_cell(i, 1, "2026-07-15")
        print(f"Satir {i} duzeltildi: tarih 2026-07-15 yapildi")
        break
else:
    print("Satir bulunamadi")
