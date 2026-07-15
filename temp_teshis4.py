from common import get_sheet, get_gorevler_sheet

# 1) Sabah telefonsuzluğu verisini kontrol et
ws = get_sheet()
rows = ws.get_all_records()
sabah_kayitlari = [r for r in rows if r.get("Görev") == "Sabah telefonsuzluğu"]

with open("teshis4_sonuc.txt", "w", encoding="utf-8") as f:
    f.write(f"Sabah telefonsuzlugu kayit sayisi: {len(sabah_kayitlari)}\n")
    for r in sabah_kayitlari:
        f.write(f"  {r['Tarih']} {r['Saat']} - {r['Durum']}\n")

# 2) Bugunku (15 Temmuz) yanlis basligi temizle
ws2 = get_gorevler_sheet()
rows2 = ws2.get_all_values()
for i, row in enumerate(rows2[1:], start=2):
    if row[0] == "2026-07-15" and row[2] == "Günaydın, bugünün görevlerini yazıyorum":
        ws2.delete_rows(i)
        with open("teshis4_sonuc.txt", "a", encoding="utf-8") as f:
            f.write(f"\nSatir {i} silindi.\n")
        break
