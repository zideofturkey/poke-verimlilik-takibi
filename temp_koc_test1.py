"""GEÇİCİ TEST 1/2 - 'tekrarlanan görev -> rutin' mekanizmasını test eder.
Sentetik veri ekler, tespit fonksiyonunu çalıştırır, kullanılan hash'i yazdırır."""
import hashlib
from common import get_gorevler_sheet, guvenli_append_row
import analiz

TEST_METIN = "test kocrutin gorevi zzz"

def main():
    ws = get_gorevler_sheet()
    for tarih in ["2026-06-01", "2026-06-02", "2026-06-03"]:
        guvenli_append_row(ws, [tarih, "", TEST_METIN, "Yapıldı"])
    print("3 sentetik satır eklendi.")

    analiz.tekrarlanan_gorev_oruntu_sun()

    hash6 = hashlib.sha1(TEST_METIN.lower().encode()).hexdigest()[:6]
    print(f"Beklenen hash: {hash6}")
    print(f"callback_data (evet): kocgorevrutin_{hash6}_evet")

if __name__ == "__main__":
    main()
