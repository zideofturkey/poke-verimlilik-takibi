"""GEÇİCİ KONTROL."""
from common import get_sheet

def main():
    spreadsheet = get_sheet().spreadsheet
    ws = spreadsheet.worksheet("SLMLog")
    print("=== SLMLog (son karar) ===")
    for r in ws.get_all_values()[-1:]:
        print(r[:4])

if __name__ == "__main__":
    main()
