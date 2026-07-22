"""GEÇİCİ DOĞRULAMA - son replay sonucunu kontrol eder."""
from common import get_sheet

def main():
    spreadsheet = get_sheet().spreadsheet
    print("=== SLMLog (son 2 karar) ===")
    slm_ws = spreadsheet.worksheet("SLMLog")
    for r in slm_ws.get_all_values()[-2:]:
        print(r[:4])

    print("\n=== HataLog (son 3 kayıt) ===")
    hata_ws = spreadsheet.worksheet("HataLog")
    for r in hata_ws.get_all_values()[-3:]:
        print(r)

    print("\n=== AnlasmazlikLog (varsa) ===")
    try:
        an_ws = spreadsheet.worksheet("AnlasmazlikLog")
        rows = an_ws.get_all_values()
        print(f"Toplam {len(rows)-1} kayıt")
        for r in rows[-3:]:
            print(r)
    except Exception as e:
        print("Sekme yok:", e)

if __name__ == "__main__":
    main()
