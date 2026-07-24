"""GEÇİCİ SON DOĞRULAMA."""
import datetime
from common import get_gorevler_sheet, TR_TZ, get_sheet

def main():
    bugun = datetime.datetime.now(TR_TZ).strftime("%Y-%m-%d")
    ws = get_gorevler_sheet()
    print(f"=== Bugün ({bugun}) GunlukGorevler ===")
    for i, r in enumerate(ws.get_all_values()):
        if i == 0 or (r and r[0] == bugun):
            print(i + 1, r)

    print("\n=== SLMLog (son karar) ===")
    spreadsheet = get_sheet().spreadsheet
    slm_ws = spreadsheet.worksheet("SLMLog")
    for r in slm_ws.get_all_values()[-1:]:
        print(r[:4])

    print("\n=== AnlasmazlikLog (son 2, varsa) ===")
    try:
        an_ws = spreadsheet.worksheet("AnlasmazlikLog")
        rows = an_ws.get_all_values()
        for r in rows[-2:]:
            print(r)
    except Exception as e:
        print("yok:", e)

if __name__ == "__main__":
    main()
