"""GEÇİCİ DOĞRULAMA+TEMİZLİK 1/2 - 'tekrarlanan görev -> rutin'
mekanizmasının gerçekten Rutinler'e satır eklediğini doğrular, sonra
tüm sentetik veriyi (görevler + yeni rutin) temizler."""
from common import get_gorevler_sheet, get_rutinler_sheet

TEST_METIN = "test kocrutin gorevi zzz"

def main():
    ws_rutin = get_rutinler_sheet()
    rows = ws_rutin.get_all_values()
    print("=== Rutinler sekmesi (test kaydı var mı?) ===")
    silinecek_rutin_satiri = None
    for i, row in enumerate(rows):
        if len(row) >= 2 and row[1] == TEST_METIN:
            print(f"BULUNDU: satır {i+1} -> {row}")
            silinecek_rutin_satiri = i + 1

    ws_gorev = get_gorevler_sheet()
    gorev_rows = ws_gorev.get_all_values()
    silinecek_gorev_satirlari = [
        i + 1 for i, row in enumerate(gorev_rows)
        if len(row) >= 3 and row[2] == TEST_METIN
    ]
    print(f"\nSilinecek görev satırları: {silinecek_gorev_satirlari}")

    # Temizlik - büyük satır no'dan küçüğe doğru sil
    for satir_no in sorted(silinecek_gorev_satirlari, reverse=True):
        ws_gorev.delete_rows(satir_no)
    print("Sentetik görev satırları silindi.")

    if silinecek_rutin_satiri:
        ws_rutin.delete_rows(silinecek_rutin_satiri)
        print("Sentetik rutin satırı silindi.")

if __name__ == "__main__":
    main()
