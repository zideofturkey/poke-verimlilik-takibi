"""GEÇİCİ DOĞRULAMA - gönderim gerçekten oldu mu, geçmiş sekmesine
yazıldı mı kontrol eder."""
from common import get_deger, get_aforizma_gecmis_sheet

def main():
    print("aforizma_son_gonderim:", get_deger("aforizma_son_gonderim"))

    print("\n=== AforizmaGecmis (son 3) ===")
    ws = get_aforizma_gecmis_sheet()
    for r in ws.get_all_values()[-3:]:
        print(" ", r)

if __name__ == "__main__":
    main()
