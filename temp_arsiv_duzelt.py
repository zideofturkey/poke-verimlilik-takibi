"""GEÇİCİ - HaftalikHedefArsiv'in bozuk (başlıksız, mükerrer) halini
düzeltir: benzersiz satırları çıkarır, sekmeyi silip doğru başlıkla
yeniden oluşturur, benzersiz veriyi geri yazar."""
from common import get_sheet, guvenli_append_row

spreadsheet = get_sheet().spreadsheet
ws = spreadsheet.worksheet("HaftalikHedefArsiv")
ham = ws.get_all_values()

with open("gecici_arsiv_duzelt_sonuc.txt", "w", encoding="utf-8") as f:
    f.write(f"Düzeltme ÖNCESİ satır sayısı: {len(ham)}\n")

    # Benzersiz (HaftaBaslangic, HedefMetni, Durum) üçlülerini çıkar,
    # sırayı koru (ilk görülen sırada)
    gorulen = set()
    benzersiz = []
    for satir in ham:
        anahtar = tuple(satir)
        if anahtar not in gorulen:
            gorulen.add(anahtar)
            benzersiz.append(satir)

    f.write(f"Benzersiz satır sayısı: {len(benzersiz)}\n")
    for s in benzersiz:
        f.write(f"{s}\n")

    # Sekmeyi sil, doğru başlıkla yeniden oluştur
    spreadsheet.del_worksheet(ws)
    yeni_ws = spreadsheet.add_worksheet(title="HaftalikHedefArsiv", rows=3000, cols=4)
    basliklar = ["HaftaBaslangic", "HedefMetni", "Durum"]
    guvenli_append_row(yeni_ws, basliklar)

    # Doğrula
    kontrol = yeni_ws.get_all_values()
    f.write(f"\nYeniden oluşturulan sekme ilk satırı: {kontrol[0] if kontrol else 'BOŞ'}\n")
    assert kontrol and kontrol[0] == basliklar, "Başlık doğrulanamadı!"

    # Benzersiz veriyi geri yaz (toplu)
    if benzersiz:
        yeni_ws.append_rows(benzersiz)

    son_durum = yeni_ws.get_all_values()
    f.write(f"\nDüzeltme SONRASI satır sayısı: {len(son_durum)}\n")
    for s in son_durum:
        f.write(f"{s}\n")

print("Düzeltme tamamlandı.")
