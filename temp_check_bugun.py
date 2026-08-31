import datetime
from common import get_gorevler_sheet, TR_TZ

bugun = datetime.datetime.now(TR_TZ).strftime("%Y-%m-%d")
ws = get_gorevler_sheet()
rows = ws.get_all_records()
bugunku = [r for r in rows if r["Tarih"] == bugun]
print(f"Bugun ({bugun}) icin satir sayisi: {len(bugunku)}")
for r in bugunku:
    print(r)
