"""GEÇİCİ KONTROL - bugünün mevcut görev sayısına bakar (test öncesi baseline)."""
from common import get_gorevler_sheet, bugun_str

def main():
    bugun = bugun_str()
    ws = get_gorevler_sheet()
    rows = ws.get_all_records()
    bugunku = [r for r in rows if r.get("Tarih") == bugun]
    print(f"Bugün ({bugun}) için {len(bugunku)} görev var:")
    for r in bugunku:
        print(" ", r)

if __name__ == "__main__":
    main()
