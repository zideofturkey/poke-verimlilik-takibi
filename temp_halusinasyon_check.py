"""GEÇİCİ DOĞRULAMA - SLM'in ham çıktısını gösterir, halüsinasyon
tekrarlandı mı görmek için."""
from common import get_sheet

def main():
    spreadsheet = get_sheet().spreadsheet
    ws = spreadsheet.worksheet("SLMLog")
    rows = ws.get_all_values()
    for r in rows:
        if len(r) > 3 and "1 saat 50 dakika" in r[3]:
            print("Bulundu:", r[0], r[1], r[2])
            print("Kolon 3:", r[3])
            if len(r) > 4:
                print("Kolon 4 (tam prompt+cevap):")
                print(r[4])

if __name__ == "__main__":
    main()
