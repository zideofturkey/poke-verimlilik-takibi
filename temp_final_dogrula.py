"""GEÇİCİ SON DOĞRULAMA + TEMİZLİK."""
import datetime
from common import get_gorevler_sheet, TR_TZ, get_sheet

def main():
    bugun = datetime.datetime.now(TR_TZ).strftime("%Y-%m-%d")
    ws = get_gorevler_sheet()
    rows = ws.get_all_values()
    print(f"=== Bugün ({bugun}) GunlukGorevler ===")
    for i, r in enumerate(rows):
        if i == 0 or (r and r[0] == bugun):
            print(i + 1, r)

    print("\n=== SLMLog (son karar) ===")
    spreadsheet = get_sheet().spreadsheet
    slm_ws = spreadsheet.worksheet("SLMLog")
    for r in slm_ws.get_all_values()[-1:]:
        print(r[:4])

    # Temizlik
    for i, r in enumerate(rows):
        if r and r[0] == bugun and len(r) >= 3 and "test dogrulama gorevi" in r[2]:
            ws.delete_rows(i + 1)
            print(f"\nTest satırı silindi: satır {i+1} -> {r}")

if __name__ == "__main__":
    main()
