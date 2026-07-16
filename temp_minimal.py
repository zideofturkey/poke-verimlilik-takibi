from common import get_deger
try:
    v = get_deger("bekleyen_soru_tarihi")
    with open("minimal_sonuc.txt", "w") as f:
        f.write(f"BASARILI: {v}")
except Exception as e:
    import traceback
    with open("minimal_sonuc.txt", "w") as f:
        f.write(f"HATA: {e}\n{traceback.format_exc()}")
print("bitti")
