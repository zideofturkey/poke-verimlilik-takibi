"""GEÇİCİ TEMİZLİK SCRIPTİ - iş bitince silinecek.
Yanlış sınıflandırma bug'ı yüzünden GunlukGorevler'e görev olarak
kaydedilmiş 3 sorgu cümlesini siler.
"""
from common import get_gorevler_sheet

HEDEF_SATIRLAR = [
    ("2026-07-20", "Bugünkü görevlerimi sorguluyorum"),
    ("2026-07-20", "Sil son aldığın notu. Bugünkü görevlerimi listele"),
    ("2026-07-22", "günlük görevlerimi sorgula lütfen"),
]

def main():
    ws = get_gorevler_sheet()
    rows = ws.get_all_values()  # 1. satır header
    to_delete = []  # (sheet_row_number, tarih, metin)

    for idx, row in enumerate(rows):
        if idx == 0:
            continue  # header
        if len(row) < 3:
            continue
        tarih, _, metin = row[0], row[1], row[2]
        for h_tarih, h_metin in HEDEF_SATIRLAR:
            if tarih == h_tarih and metin.strip() == h_metin.strip():
                to_delete.append((idx + 1, tarih, metin))  # +1: gspread 1-indexed

    print(f"Silinecek {len(to_delete)} satır bulundu:")
    for r in to_delete:
        print(" ", r)

    # Büyük satır numarasından küçüğe doğru sil (indeks kaymasını önlemek için)
    for row_num, tarih, metin in sorted(to_delete, key=lambda x: -x[0]):
        ws.delete_rows(row_num)
        print(f"Silindi: satır {row_num} ({tarih} - {metin})")

    print("Tamamlandı.")

if __name__ == "__main__":
    main()
