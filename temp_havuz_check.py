"""GEÇİCİ DOĞRULAMA - yeni 100 sözlük havuzdan seçim yapan aforizma_sec()
fonksiyonunun hatasız çalıştığını ve doğru formatta veri döndürdüğünü
kontrol eder (birkaç kez çağırıp çeşitliliği de gösterir)."""
from common import aforizma_sec

def main():
    for i in range(5):
        secilen = aforizma_sec()
        print(f"{i+1}) \"{secilen['soz']}\" — {secilen['yazar']}")

if __name__ == "__main__":
    main()
