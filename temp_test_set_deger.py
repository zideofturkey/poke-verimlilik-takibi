from common import set_deger, get_deger

# Normal calisma yolunu test et - retry'a hic gerek kalmadan
onceki = get_deger("test_anahtar_gecici")
print(f"Onceki deger: {onceki!r}")

set_deger("test_anahtar_gecici", "test_deger_1")
sonuc1 = get_deger("test_anahtar_gecici")
print(f"Set sonrasi (yeni satir): {sonuc1!r}")
assert sonuc1 == "test_deger_1", "Yeni satir ekleme basarisiz!"

set_deger("test_anahtar_gecici", "test_deger_2")
sonuc2 = get_deger("test_anahtar_gecici")
print(f"Set sonrasi (guncelleme): {sonuc2!r}")
assert sonuc2 == "test_deger_2", "Mevcut satir guncelleme basarisiz!"

print("TUM TESTLER GECTI")
