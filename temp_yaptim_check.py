"""GEÇİCİ KONTROL - kullanıcının 'yaptım' mesajının tam metnini ve
verilen cevabı SLMLog'dan bulur."""
from common import get_sheet

def main():
    spreadsheet = get_sheet().spreadsheet
    slm_ws = spreadsheet.worksheet("SLMLog")
    rows = slm_ws.get_all_values()
    print(f"SLMLog toplam {len(rows)-1} kayıt. Son 8 tanesi:")
    for r in rows[-8:]:
        print(r[:4])

if __name__ == "__main__":
    main()
