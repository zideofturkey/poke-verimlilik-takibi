import time
from common import get_haftalik_sheet, get_gorevler_sheet, bugun_str

def dene(fn, aciklama, deneme=4, bekleme=5):
    for i in range(deneme):
        try:
            return fn()
        except Exception as e:
            print(f"{aciklama} hata (deneme {i+1}/{deneme}): {e}")
            if i < deneme - 1:
                time.sleep(bekleme)
            else:
                raise

ws_hafta = dene(get_haftalik_sheet, "get_haftalik_sheet")
rows = dene(lambda: ws_hafta.get_all_values(), "get_all_values")

sonuc_satirlari = ["=== HaftalikHedefler (mevcut durum) ===\n"]
for i, row in enumerate(rows, start=1):
    sonuc_satirlari.append(f"{i}: {row}\n")

yanlis_satir_nolari = [i for i, row in enumerate(rows, start=1) if len(row) >= 1 and row[0] == "2026-07-13" and i > 7]
sonuc_satirlari.append(f"\nSilinecek satirlar: {yanlis_satir_nolari}\n")

metinler = [rows[n-1][1] for n in yanlis_satir_nolari]

for satir_no in sorted(yanlis_satir_nolari, reverse=True):
    dene(lambda sn=satir_no: ws_hafta.delete_rows(sn), f"delete_rows {satir_no}")
    time.sleep(1)

ws_gorev = dene(get_gorevler_sheet, "get_gorevler_sheet")
bugun = dene(bugun_str, "bugun_str")
for metin in metinler:
    dene(lambda m=metin: ws_gorev.append_row([bugun, "", m, "Bekliyor"]), f"append_row {metin}")
    time.sleep(1)

sonuc_satirlari.append(f"\nGunlukGorevler'e eklenenler: {metinler}\n")

with open("final_sonuc.txt", "w", encoding="utf-8") as f:
    f.writelines(sonuc_satirlari)
print("TAMAMLANDI")
