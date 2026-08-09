"""GEÇİCİ DOĞRULAMA+TEMİZLİK 2/2 - limitin gerçekten değiştiğini
doğrular, sonra sentetik 'Boşa geçen vakit' kayıtlarını temizler ve
limiti varsayılana (90) geri döndürür."""
import datetime
from common import get_sheet, sosyal_medya_limit_dakika, sosyal_medya_limit_ayarla, TR_TZ

TEST_DETAY = "150 dakika sosyal medyada test verisi"

def main():
    print("Değişim sonrası limit:", sosyal_medya_limit_dakika())

    ws = get_sheet()
    rows = ws.get_all_values()
    silinecek = [i + 1 for i, row in enumerate(rows) if len(row) >= 5 and row[4] == TEST_DETAY]
    print("Silinecek sentetik satırlar:", silinecek)
    for satir_no in sorted(silinecek, reverse=True):
        ws.delete_rows(satir_no)
    print("Sentetik boşa-vakit satırları silindi.")

    sosyal_medya_limit_ayarla(90)
    print("Limit varsayılana (90) geri döndürüldü:", sosyal_medya_limit_dakika())

if __name__ == "__main__":
    main()
