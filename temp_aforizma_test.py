"""GEÇİCİ DOĞRULAMA - kullanıcı eklemesinin gerçekten kaydedildiğini kontrol eder."""
from common import get_aforizma_kullanici_sheet

def main():
    ws = get_aforizma_kullanici_sheet()
    print("=== AforizmaKullanici (tüm satırlar) ===")
    for r in ws.get_all_values():
        print(" ", r)

if __name__ == "__main__":
    main()
