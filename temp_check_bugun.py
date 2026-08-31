from common import get_gorevler_sheet, bugun_str

ws = get_gorevler_sheet()
rows = ws.get_all_records()
bugun = bugun_str()
bugunku = [r for r in rows if r["Tarih"] == bugun]
print(f"Bugun ({bugun}) icin satir sayisi: {len(bugunku)}")
for r in bugunku:
    print(r)
