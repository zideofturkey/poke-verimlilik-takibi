from common import get_haftalik_sheet

ws = get_haftalik_sheet()
sh = ws.spreadsheet

kullanicinin_verdigi_id = "1OG79C8K1TgEEstOKUF7qMpr6N4q0iezBXBuP5-8SiSs"
print("AYNI SPREADSHEET MI?:", sh.id == kullanicinin_verdigi_id)
print("BASLIK:", sh.title)

rows = ws.get_all_values()
print("TOPLAM SATIR SAYISI (header dahil):", len(rows))
for r in rows:
    print(r)
