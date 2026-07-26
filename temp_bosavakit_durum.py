"""GEÇİCİ KONTROL - bugünkü görev/rutin durumunu gösterir (test
senaryolarını gerçekçi kurmak için)."""
import datetime
from common import get_gorevler_sheet, get_sheet, get_aktif_rutinler, cevaplanan_rutinler, TR_TZ

def main():
    bugun = datetime.datetime.now(TR_TZ).strftime("%Y-%m-%d")
    print(f"=== Bugün ({bugun}) görevleri ===")
    ws = get_gorevler_sheet()
    for r in ws.get_all_records():
        if r.get("Tarih") == bugun:
            print(" ", r)

    print("\n=== Aktif rutinler ve bugünkü durumları ===")
    ws2 = get_sheet()
    rutin_durumlari = {r["Görev"]: r["Durum"] for r in ws2.get_all_records() if r.get("Tarih") == bugun}
    for rutin in get_aktif_rutinler():
        print(" ", rutin["isim"], "->", rutin_durumlari.get(rutin["isim"], "CEVAPSIZ"))

if __name__ == "__main__":
    main()
