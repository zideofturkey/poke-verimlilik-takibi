from common import get_haftalik_sheet, get_gorevler_sheet, bugun_str

ws_hafta = get_haftalik_sheet()
# Satirlar 8,9,10,11,12 (1-indexed) - yanlislikla haftalik hedeflere eklenmis
# gunluk gorevler. Once metinlerini oku, sonra sondan basa dogru sil.
satir_no_listesi = [8, 9, 10, 11, 12]
metinler = []
for satir_no in satir_no_listesi:
    deger = ws_hafta.cell(satir_no, 2).value
    metinler.append(deger)

for satir_no in sorted(satir_no_listesi, reverse=True):
    ws_hafta.delete_rows(satir_no)

ws_gorev = get_gorevler_sheet()
bugun = bugun_str()
for metin in metinler:
    ws_gorev.append_row([bugun, "", metin, "Bekliyor"])

with open("duzelt8_sonuc.txt", "w", encoding="utf-8") as f:
    f.write(f"Silinen satirlar: {satir_no_listesi}\n")
    f.write(f"GunlukGorevler'e eklenenler: {metinler}\n")
print("tamamlandi")
