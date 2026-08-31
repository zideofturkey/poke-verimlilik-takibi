from common import set_deger, get_deger

onceki = get_deger("son_sabah_tarihi")
print(f"Onceki deger: {onceki!r}")
set_deger("son_sabah_tarihi", "2026-08-30")  # dunku tarihe geri al
print(f"Yeni deger: {get_deger('son_sabah_tarihi')!r}")
