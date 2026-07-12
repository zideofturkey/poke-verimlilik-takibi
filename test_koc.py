import datetime
from common import get_sheet, TR_TZ

ws = get_sheet()
bugun = datetime.datetime.now(TR_TZ).date()
for gun_farki in range(1, 6):  # dun'den 5 gun once'ye kadar
    tarih = (bugun - datetime.timedelta(days=gun_farki)).strftime("%Y-%m-%d")
    ws.append_row([tarih, "12:00", "Verimli video izleme", "Yapılmadı", "TEST_VERI"])
print("5 gunluk sentetik kacirma verisi eklendi.")
