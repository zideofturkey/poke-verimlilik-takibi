from common import set_deger, TR_TZ
import datetime
bugun = datetime.datetime.now(TR_TZ).strftime("%Y-%m-%d")
set_deger("son_sabah_tarihi", bugun)
print(f"Isaretlendi: {bugun}")
