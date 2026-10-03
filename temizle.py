"""
Eski verileri temizler. Haftalık olarak (Pazartesi) GitHub Actions
tarafından otomatik çalıştırılır, istenirse manuel de tetiklenebilir.

Saklama kuralları:
    - GunlukGorevler: 15 günden eski satırlar silinir
      (telafi mantığı en fazla birkaç gün geriye bakıyor, daha eskisi gereksiz)
    - HaftalikHedefler: 14 günden eski satırlar silinir
      (bu hafta + geçen hafta karşılaştırması için yeterli)
    - CopKutusu: 7 günden eski satırlar KALICI olarak silinir
      (GOREV_SIL ile silinen görev/hedeflerin soft-delete çöp kutusu -
      kullanıcının isteğiyle 7 gün geri alınabilir tutuluyor, sonra kalıcı siliniyor)
    - Takip (ana log): DOKUNULMAZ - bu, uzun vadeli istatistik/streak/pattern
      analizi için kalıcı geçmiş, silinmez.
"""

import datetime
from common import get_gorevler_sheet, get_haftalik_sheet, get_cop_kutusu_sheet, TR_TZ

GUNLUK_SAKLAMA_GUNU = 15
HAFTALIK_SAKLAMA_GUNU = 14
COP_KUTUSU_SAKLAMA_GUNU = 7


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


def temizle_cop_kutusu():
    """CopKutusu'nda (GOREV_SIL ile soft-delete edilen satırlar) 7 günden
    eski olanları KALICI olarak siler - temizle_gunluk/temizle_haftalik
    İLE BİREBİR AYNI desen, sadece SilinmeTarihi sütununa (ilk sütun,
    diğer iki fonksiyondaki Tarih/HaftaBaslangic ile aynı konumda) bakıyor."""
    ws = get_cop_kutusu_sheet()
    rows = ws.get_all_values()
    if len(rows) <= 1:
        print("CopKutusu: silinecek bir şey yok.")
        return

    bugun = datetime.datetime.now(TR_TZ).date()
    sinir = bugun - datetime.timedelta(days=COP_KUTUSU_SAKLAMA_GUNU)

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
        print("CopKutusu: 7 günden eski satır yok.")
        return

    for satir_no in reversed(silinecek_satirlar):
        ws.delete_rows(satir_no)

    print(f"CopKutusu: {len(silinecek_satirlar)} eski satır kalıcı olarak silindi.")


def main():
    temizle_gunluk()
    temizle_haftalik()
    temizle_cop_kutusu()


if __name__ == "__main__":
    main()
