from common import get_sheet

ws = get_sheet()
rows = ws.get_all_records()

koc_satirlari = [r for r in rows if str(r.get("Görev", "")).startswith("Koç kararı:")]

with open("gecici_koc_teshis.txt", "w", encoding="utf-8") as f:
    f.write(f"Takip sheet toplam satır: {len(rows)}\n")
    f.write(f"'Koç kararı:' ile başlayan satır sayısı: {len(koc_satirlari)}\n\n")
    for r in koc_satirlari:
        f.write(f"{r}\n")

    # Ayrıca miss_streak'i 5+ olan bir rutin var mı diye kontrol edelim
    from common import get_aktif_rutinler, rutin_serisi_hesapla
    f.write("\n=== ŞU ANKİ MISS STREAK DURUMU (tüm aktif günlük rutinler) ===\n")
    for rutin in get_aktif_rutinler():
        streak, miss_streak = rutin_serisi_hesapla(rutin["isim"])
        f.write(f"{rutin['isim']}: streak={streak}, miss_streak={miss_streak}\n")

print("Teşhis tamamlandı.")
