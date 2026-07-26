"""GEÇİCİ KONTROL - SLM'in FAYDALI_DAKIKA alanını doğru çıkarıp
çıkarmadığını, ham promptun tamamına bakarak kontrol eder."""
from common import get_sheet

def main():
    spreadsheet = get_sheet().spreadsheet
    ws = spreadsheet.worksheet("SLMLog")
    rows = ws.get_all_values()
    print("Son satırın TAM içeriği:")
    son = rows[-1]
    for i, deger in enumerate(son):
        print(f"kolon {i}: {deger[:500]}")

if __name__ == "__main__":
    main()
