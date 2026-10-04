from common import get_haftalik_sheet, hafta_baslangic_str

ws = get_haftalik_sheet()
hafta = hafta_baslangic_str()
rows = ws.get_all_records()
print("Bu hafta:", hafta)
for i, r in enumerate(rows):
    if r.get("HaftaBaslangic") == hafta:
        print(f"satir {i+2}: {r}")
