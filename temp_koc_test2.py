"""GEÇİCİ TEST 2/2 - 'boşa vakit trend' mekanizmasını sentetik veriyle
tetikler: son 10 günden 4 gün için sınırı aşan 'Boşa geçen vakit'
kayıtları ekler, sonra tespit fonksiyonunu çalıştırır."""
import datetime
from common import get_sheet, guvenli_append_row, TR_TZ

def main():
    ws = get_sheet()
    bugun = datetime.datetime.now(TR_TZ).date()
    eklenen_satirlar = []
    # Son 10 günün İÇİNDEN 4 farklı, henüz veri olmayan güne (sınırın
    # ÜZERİNDE, 150 dakika) sentetik kayıt ekleyelim.
    for i in [2, 4, 6, 8]:
        tarih = (bugun - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
        guvenli_append_row(ws, [tarih, "", "Boşa geçen vakit", "Beyan", "150 dakika sosyal medyada test verisi"])
        eklenen_satirlar.append(tarih)
    print("Eklenen sentetik günler:", eklenen_satirlar)

if __name__ == "__main__":
    main()
