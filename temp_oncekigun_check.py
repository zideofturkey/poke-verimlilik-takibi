"""GEÇİCİ DOĞRULAMA - tarihler-arası sorgunun düzgün tetiklenip
tetiklenmediğini kontrol eder."""
from common import get_sheet

def main():
    spreadsheet = get_sheet().spreadsheet
    print("=== SLMLog (son karar) ===")
    slm_ws = spreadsheet.worksheet("SLMLog")
    for r in slm_ws.get_all_values()[-1:]:
        print(r[:4])

if __name__ == "__main__":
    main()
