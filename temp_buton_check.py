"""GEÇİCİ SON KONTROL - buton testinin sonucunu doğrular."""
from common import get_sheet

def main():
    spreadsheet = get_sheet().spreadsheet
    print("=== SLMLog (son karar) ===")
    slm_ws = spreadsheet.worksheet("SLMLog")
    for r in slm_ws.get_all_values()[-1:]:
        print(r[:4])

    print("\n=== HataLog (son 3 - yeni hata var mı?) ===")
    hata_ws = spreadsheet.worksheet("HataLog")
    for r in hata_ws.get_all_values()[-3:]:
        print(r)

if __name__ == "__main__":
    main()
