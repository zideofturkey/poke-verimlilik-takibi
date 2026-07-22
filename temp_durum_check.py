"""GEÇİCİ KONTROL - 22 Temmuz'un mevcut görev/rutin durumunu gösterir
(interaktif buton testinden önce, hangi öğelerin hâlâ Bekliyor olduğunu
görmek için)."""
from common import get_gorevler_sheet, get_sheet, get_aktif_rutinler, cevaplanan_rutinler

def main():
    tarih = "2026-07-22"
    print(f"=== {tarih} GunlukGorevler ===")
    ws = get_gorevler_sheet()
    for r in ws.get_all_records():
        if r.get("Tarih") == tarih:
            print(r)

    print(f"\n=== {tarih} Rutin takip (Durum sekmesi) ===")
    ws2 = get_sheet()
    rutin_isimleri = {r["isim"] for r in get_aktif_rutinler()}
    for r in ws2.get_all_records():
        if r.get("Tarih") == tarih and r.get("Görev") in rutin_isimleri:
            print(r)

    print(f"\n=== {tarih} için cevaplanan rutinler ===")
    print(cevaplanan_rutinler(tarih))
    print("Aktif rutinler:", [r["isim"] for r in get_aktif_rutinler()])

if __name__ == "__main__":
    main()
