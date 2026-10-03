from common import get_sheet

spreadsheet = get_sheet().spreadsheet
with open("gecici_sheet_liste.txt", "w", encoding="utf-8") as f:
    f.write("=== TÜM WORKSHEET'LER ===\n")
    for ws in spreadsheet.worksheets():
        f.write(f"id={ws.id} title='{ws.title}' rows={ws.row_count} cols={ws.col_count}\n")

    f.write("\n=== HaftalikHedefArsiv - get_all_values (ham) ===\n")
    ws = spreadsheet.worksheet("HaftalikHedefArsiv")
    f.write(f"Bulunan sekme id={ws.id}\n")
    ham = ws.get_all_values()
    f.write(f"Satır sayısı: {len(ham)}\n")
    for satir in ham:
        f.write(f"{satir}\n")

    f.write("\n=== HaftalikHedefArsiv - get_all_records ===\n")
    import json
    f.write(json.dumps(ws.get_all_records(), ensure_ascii=False, indent=2))

print("Tamamlandı.")
