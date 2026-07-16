import time
from common import get_haftalik_sheet, get_gorevler_sheet, bugun_str

log = []

try:
    ws_hafta = get_haftalik_sheet()
    log.append("get_haftalik_sheet OK")

    # Tek tek, yavas yavas sil (8,9,10,11,12 - buyukten kucuge)
    metinler = []
    for satir_no in [12, 11, 10, 9, 8]:
        deger = ws_hafta.cell(satir_no, 2).value
        metinler.append(deger)
        log.append(f"okundu satir {satir_no}: {deger}")
        time.sleep(3)
        ws_hafta.delete_rows(satir_no)
        log.append(f"silindi satir {satir_no}")
        time.sleep(3)

    ws_gorev = get_gorevler_sheet()
    bugun = bugun_str()
    for metin in reversed(metinler):
        ws_gorev.append_row([bugun, "", metin, "Bekliyor"])
        log.append(f"eklendi gorev: {metin}")
        time.sleep(3)

    log.append("HEPSI TAMAMLANDI")
except Exception as e:
    import traceback
    log.append(f"HATA: {e}")
    log.append(traceback.format_exc())
finally:
    with open("yavas_sonuc.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(log))
    print("bitti, log yazildi")
