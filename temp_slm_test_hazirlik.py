"""GEÇİCİ DOĞRULAMA."""
import datetime
from common import get_gorevler_sheet, TR_TZ

def main():
    ws = get_gorevler_sheet()
    print("=== 20 Temmuz görevleri ===")
    for r in ws.get_all_records():
        if r.get("Tarih") == "2026-07-20":
            print(" ", r)

    bugun = datetime.datetime.now(TR_TZ).strftime("%Y-%m-%d")
    print(f"\n=== Bugün ({bugun}) - sahte kayıt var mı? ===")
    for r in ws.get_all_records():
        if r.get("Tarih") == bugun:
            print(" ", r)

if __name__ == "__main__":
    main()
