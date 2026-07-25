"""GEÇİCİ DOĞRULAMA."""
import datetime
from common import get_gorevler_sheet, get_sheet, TR_TZ

def main():
    print("=== 20 Temmuz görevleri ===")
    ws = get_gorevler_sheet()
    for r in ws.get_all_records():
        if r.get("Tarih") == "2026-07-20":
            print(" ", r)

    bugun = datetime.datetime.now(TR_TZ).strftime("%Y-%m-%d")
    print(f"\n=== Bugün ({bugun}) görevleri (sahte kayıt oluştu mu?) ===")
    for r in ws.get_all_records():
        if r.get("Tarih") == bugun:
            print(" ", r)

    print("\n=== SLMLog (son 2 karar) ===")
    spreadsheet = get_sheet().spreadsheet
    slm_ws = spreadsheet.worksheet("SLMLog")
    for r in slm_ws.get_all_values()[-2:]:
        print(r[:4])

    print("\n=== AnlasmazlikLog (son 2) ===")
    an_ws = spreadsheet.worksheet("AnlasmazlikLog")
    for r in an_ws.get_all_values()[-2:]:
        print(r)

if __name__ == "__main__":
    main()
