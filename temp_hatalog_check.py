"""GEÇİCİ TEŞHİS - HataLog sekmesindeki gerçek hata geçmişini gösterir
(git'e bağlı olmayan, bağımsız kayıt yolu - son_hata.txt'nin git reset
--hard yüzünden neden hep eski kaldığını doğrulamak için)."""
from common import get_sheet

def main():
    spreadsheet = get_sheet().spreadsheet
    ws = spreadsheet.worksheet("HataLog")
    rows = ws.get_all_values()
    print(f"HataLog toplam {len(rows)-1} kayıt içeriyor.")
    print("Son 15 kayıt:")
    for r in rows[-15:]:
        print(r)

if __name__ == "__main__":
    main()
