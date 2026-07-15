from common import get_sheet
ws = get_sheet()
rows = ws.get_all_values()
for i, row in enumerate(rows[1:], start=2):
    if row[0] == "2026-07-14" and row[2] == "Fransızca çalışma" and row[3] == "Yapılmadı":
        ws.update_cell(i, 4, "Telafi")
        ws.update_cell(i, 5, "ertesi gün telafi edildi")
        print(f"14 Temmuz satiri ({i}) Telafi yapildi")
    if row[0] == "2026-07-15" and row[2] == "Fransızca çalışma" and row[3] == "Telafi":
        ws.update_cell(i, 4, "Yapıldı")
        print(f"15 Temmuz satiri ({i}) Yapildi yapildi")
