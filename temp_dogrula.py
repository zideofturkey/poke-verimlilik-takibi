from common import slm_sorgula
try:
    cevap = slm_sorgula("Merhaba de, tek kelime yaz.")
    with open("dogrulama_sonucu.txt", "w") as f:
        f.write(f"BASARILI: {cevap}")
except Exception as e:
    with open("dogrulama_sonucu.txt", "w") as f:
        f.write(f"HATA: {e}")
