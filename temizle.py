"""
Eski verileri temizler. Haftalık olarak (Pazartesi) GitHub Actions
tarafından otomatik çalıştırılır, istenirse manuel de tetiklenebilir.

Saklama kuralları:
    - GunlukGorevler: 15 günden eski satırlar silinir
      (telafi mantığı en fazla birkaç gün geriye bakıyor, daha eskisi gereksiz)
    - HaftalikHedefler: 14 günden eski satırlar silinir
      (bu hafta + geçen hafta karşılaştırması için yeterli)
    - Takip (ana log): DOKUNULMAZ - bu, uzun vadeli istatistik/streak/pattern
      analizi için kalıcı geçmiş, silinmez.
"""

import datetime
from common import get_gorevler_sheet, get_haftalik_sheet, TR_TZ

GUNLUK_SAKLAMA_GUNU = 15
HAFTALIK_SAKLAMA_GUNU = 14


def temizle_gunluk():
    ws = get_gorevler_sheet()
    rows = ws.get_all_values()
    if len(rows) <= 1:
        print("GunlukGorevler: silinecek bir şey yok.")
        return

    bugun = datetime.datetime.now(TR_TZ).date()
    sinir = bugun - datetime.timedelta(days=GUNLUK_SAKLAMA_GUNU)

    silinecek_satirlar = []
    for i, row in enumerate(rows[1:], start=2):  # 1: başlık, satırlar 2'den başlar
        tarih_str = row[0]
        try:
            tarih = datetime.datetime.strptime(tarih_str, "%Y-%m-%d").date()
        except ValueError:
            continue
        if tarih < sinir:
            silinecek_satirlar.append(i)

    if not silinecek_satirlar:
        print("GunlukGorevler: 15 günden eski satır yok.")
        return

    # Sondan başa doğru sil (yoksa satır numaraları kayar)
    for satir_no in reversed(silinecek_satirlar):
        ws.delete_rows(satir_no)

    print(f"GunlukGorevler: {len(silinecek_satirlar)} eski satır silindi.")


def temizle_haftalik():
    ws = get_haftalik_sheet()
    rows = ws.get_all_values()
    if len(rows) <= 1:
        print("HaftalikHedefler: silinecek bir şey yok.")
        return

    bugun = datetime.datetime.now(TR_TZ).date()
    sinir = bugun - datetime.timedelta(days=HAFTALIK_SAKLAMA_GUNU)

    silinecek_satirlar = []
    for i, row in enumerate(rows[1:], start=2):
        tarih_str = row[0]
        try:
            tarih = datetime.datetime.strptime(tarih_str, "%Y-%m-%d").date()
        except ValueError:
            continue
        if tarih < sinir:
            silinecek_satirlar.append(i)

    if not silinecek_satirlar:
        print("HaftalikHedefler: 14 günden eski satır yok.")
        return

    for satir_no in reversed(silinecek_satirlar):
        ws.delete_rows(satir_no)

    print(f"HaftalikHedefler: {len(silinecek_satirlar)} eski satır silindi.")


def main():
    temizle_gunluk()
    temizle_haftalik()


if __name__ == "__main__":
    main()
