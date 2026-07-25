"""GEÇİCİ DOĞRULAMA - tarihler-arası sorgu testinin sonucunu kontrol eder."""
from common import get_sheet, get_gorevler_sheet

def main():
    print("=== Bekleyen (Bekliyor) günlük görevler (tüm tarihler) ===")
    ws = get_gorevler_sheet()
    bekleyenler = [r for r in ws.get_all_records() if r.get("Durum") == "Bekliyor"]
    print(f"Toplam {len(bekleyenler)} bekleyen görev:")
    for r in bekleyenler:
        print(" ", r)

    print("\n=== SLMLog (son karar) ===")
    spreadsheet = get_sheet().spreadsheet
    slm_ws = spreadsheet.worksheet("SLMLog")
    for r in slm_ws.get_all_values()[-1:]:
        print(r[:4])

if __name__ == "__main__":
    main()
