"""GEÇİCİ DOĞRULAMA."""
from common import get_gorevler_sheet, get_sheet

def main():
    print("=== 20 Temmuz görevleri ===")
    ws = get_gorevler_sheet()
    for r in ws.get_all_records():
        if r.get("Tarih") == "2026-07-20":
            print(" ", r)

    print("\n=== SLMLog (son karar) ===")
    spreadsheet = get_sheet().spreadsheet
    slm_ws = spreadsheet.worksheet("SLMLog")
    for r in slm_ws.get_all_values()[-1:]:
        print(r[:4])

if __name__ == "__main__":
    main()
