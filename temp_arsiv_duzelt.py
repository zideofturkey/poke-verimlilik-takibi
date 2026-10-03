"""GEÇİCİ - arşiv sekmelerinin bozuk (başlıksız, mükerrer) hallerini
düzeltir: benzersiz satırları çıkarır, sekmeyi silip doğru başlıkla
yeniden oluşturur, benzersiz veriyi geri yazar.

NOT: GunlukGorevArsiv kontrol edildi, başlığı doğru - sadece
HaftalikHedefArsiv (daha önce düzeltildi) ve HaftalikRutinTakipArsiv
etkilenmiş."""
from common import get_sheet, guvenli_append_row

spreadsheet = get_sheet().spreadsheet

HEDEFLER = [
    ("HaftalikRutinTakipArsiv", ["HaftaBaslangic", "RutinID", "Isim", "Durum"]),
]

with open("gecici_arsiv_duzelt_sonuc.txt", "w", encoding="utf-8") as f:
    for ad, basliklar in HEDEFLER:
        f.write(f"\n{'='*20} {ad} {'='*20}\n")
        ws = spreadsheet.worksheet(ad)
        ham = ws.get_all_values()
        f.write(f"Düzeltme ÖNCESİ satır sayısı: {len(ham)}\n")

        # İlk satır zaten doğru başlıksa dokunma
        if ham and ham[0] == basliklar:
            f.write("İlk satır zaten doğru başlık - dokunulmadı.\n")
            continue

        gorulen = set()
        benzersiz = []
        for satir in ham:
            anahtar = tuple(satir)
            if anahtar not in gorulen:
                gorulen.add(anahtar)
                benzersiz.append(satir)

        f.write(f"Benzersiz satır sayısı: {len(benzersiz)}\n")

        spreadsheet.del_worksheet(ws)
        yeni_ws = spreadsheet.add_worksheet(title=ad, rows=3000, cols=len(basliklar) + 1)
        guvenli_append_row(yeni_ws, basliklar)

        kontrol = yeni_ws.get_all_values()
        f.write(f"Yeniden oluşturulan sekme ilk satırı: {kontrol[0] if kontrol else 'BOŞ'}\n")
        assert kontrol and kontrol[0] == basliklar, "Başlık doğrulanamadı!"

        if benzersiz:
            yeni_ws.append_rows(benzersiz)

        son_durum = yeni_ws.get_all_values()
        f.write(f"Düzeltme SONRASI satır sayısı: {len(son_durum)}\n")

print("Düzeltme tamamlandı.")
