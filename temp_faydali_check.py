"""GEÇİCİ KONTROL - test mesajını SLMLog'da arayıp tam PROMPT+CEVAP
içeriğini gösterir."""
from common import get_sheet

def main():
    spreadsheet = get_sheet().spreadsheet
    ws = spreadsheet.worksheet("SLMLog")
    rows = ws.get_all_values()
    for r in rows:
        if len(r) > 3 and "instagramda" in r[3].lower():
            print("Bulundu:", r[0], r[1], r[2])
            print("Kolon 3 (özet):", r[3])
            if len(r) > 4:
                print("Kolon 4 (tam prompt+cevap):")
                print(r[4])

if __name__ == "__main__":
    main()
