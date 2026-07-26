"""GEÇİCİ KONTROL+TEST - aforizma hedef saatini kontrol eder, sonra
geçmişte bir saate ayarlayıp gerçek gönderim yolunu test eder."""
import datetime
from common import get_deger, set_deger, TR_TZ

def main():
    print("aforizma_hedef_tarih:", get_deger("aforizma_hedef_tarih"))
    print("aforizma_hedef_saat:", get_deger("aforizma_hedef_saat"))
    print("aforizma_son_gonderim:", get_deger("aforizma_son_gonderim"))

    # Test için hedef saati 1 dakika öncesine çek (gerçek gönderim yolunu tetiklemek için)
    simdi = datetime.datetime.now(TR_TZ)
    gecmis = (simdi - datetime.timedelta(minutes=1)).strftime("%H:%M")
    set_deger("aforizma_hedef_saat", gecmis)
    print(f"\nTest için hedef saat {gecmis}'e çekildi.")

if __name__ == "__main__":
    main()
