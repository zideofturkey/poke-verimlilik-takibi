# _gecen_hafta_rutin_cevapsizlari_kapat, "TAM OLARAK dun son-sans mesaji
# gonderilmisse" calisiyor. Gercek tarihi degistirmeden bunu test etmek
# icin datetime.datetime.now'i "yarin" donecek sekilde monkeypatch'liyoruz -
# SADECE bu gecici test script'inde, gercek koda dokunmadan.
import datetime as real_datetime
import gonder

class SahteDatetime(real_datetime.datetime):
    @classmethod
    def now(cls, tz=None):
        gercek = real_datetime.datetime.now(tz)
        return gercek + real_datetime.timedelta(days=1)

gonder.datetime.datetime = SahteDatetime

print("--- Kapatma fonksiyonu cagriliyor (yarinmis gibi) ---")
gonder._gecen_hafta_rutin_cevapsizlari_kapat()
print("--- Tamamlandi ---")
