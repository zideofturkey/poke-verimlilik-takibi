from common import get_gorevler_sheet

ws = get_gorevler_sheet()
rows = ws.get_all_values()

# Silinecek satirlar (yeniden okuyup dogru satir no'larini buluyoruz -
# aradaki zamanda baska satirlar eklenmis/silinmis olabilir, indexe
# guvenmek yerine icerige gore tekrar ariyoruz)
hedefler = [
    ("2026-08-18", "Yucuf'un elbisesine kuru temizleme ve terzi işleri", "Bekliyor"),
    ("2026-08-18", "BaharSpot travail de reelSeo", "Bekliyor"),
]

silinecekler = []
for i, r in enumerate(rows):
    if len(r) >= 4 and (r[0], r[2], r[3]) in hedefler:
        silinecekler.append(i + 1)  # 1-indexed

print("Silinecek satirlar:", silinecekler)
# Buyukten kucuge sil ki index kaymasin
for satir_no in sorted(silinecekler, reverse=True):
    print(f"Siliniyor: satir {satir_no} -> {rows[satir_no-1]}")
    ws.delete_rows(satir_no)
