"""GEÇİCİ KONTROL - bugünün mevcut görev sayısına bakar (test öncesi baseline)."""
import datetime
from common import get_gorevler_sheet, TR_TZ

def main():
    bugun = datetime.datetime.now(TR_TZ).strftime("%Y-%m-%d")
    ws = get_gorevler_sheet()
    rows = ws.get_all_records()
    bugunku = [r for r in rows if r.get("Tarih") == bugun]
    print(f"Bugün ({bugun}) için {len(bugunku)} görev var:")
    for r in bugunku:
        print(" ", r)

if __name__ == "__main__":
    main()
