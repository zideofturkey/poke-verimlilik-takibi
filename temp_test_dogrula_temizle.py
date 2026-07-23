"""GEÇİCİ DOĞRULAMA + TEMİZLİK - test görevinin doğru sayıldığını kontrol
eder, sonra test satırını Sheets'ten siler (üretim verisini kirletmemek için)."""
import datetime
from common import get_gorevler_sheet, TR_TZ, get_sheet

def main():
    bugun = datetime.datetime.now(TR_TZ).strftime("%Y-%m-%d")
    ws = get_gorevler_sheet()
    rows = ws.get_all_values()
    print(f"=== Bugün ({bugun}) GunlukGorevler tüm satırlar ===")
    for i, r in enumerate(rows):
        if i == 0 or (r and r[0] == bugun):
            print(i + 1, r)

    print("\n=== SLMLog (son karar) ===")
    spreadsheet = get_sheet().spreadsheet
    slm_ws = spreadsheet.worksheet("SLMLog")
    for r in slm_ws.get_all_values()[-1:]:
        print(r[:4])

    # Test satırını sil (temizlik)
    silindi = False
    for i, r in enumerate(rows):
        if r and r[0] == bugun and len(r) >= 3 and r[2] == "test dogrulama gorevi":
            ws.delete_rows(i + 1)
            print(f"\nTest satırı silindi: satır {i+1}")
            silindi = True
            break
    if not silindi:
        print("\nTest satırı bulunamadı (silinecek bir şey yok).")

if __name__ == "__main__":
    main()
