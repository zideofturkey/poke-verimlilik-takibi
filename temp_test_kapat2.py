# Daha temiz yontem: sistem tarihini/monkeypatch yapmak yerine, Durum
# sekmesindeki degeri elle "dun" olarak set edip fonksiyonu NORMAL
# sekilde cagiriyoruz - boylece hicbir kutuphaneyi bozma riski yok.
import datetime
from common import set_deger, TR_TZ
import gonder

dun = (datetime.datetime.now(TR_TZ).date() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
print(f"Test icin gecen_hafta_rutin_son_sans_tarihi = {dun} (dun) olarak set ediliyor...")
set_deger("gecen_hafta_rutin_son_sans_tarihi", dun)

print("--- Kapatma fonksiyonu cagriliyor ---")
gonder._gecen_hafta_rutin_cevapsizlari_kapat()
print("--- Tamamlandi ---")
