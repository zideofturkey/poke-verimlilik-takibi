from common import get_gorevler_sheet, get_haftalik_sheet, get_durum_sheet, send_message

beklenen = {
    "GunlukGorevler": ["Tarih", "GorevID", "GorevMetni", "Durum"],
    "HaftalikHedefler": ["HaftaBaslangic", "HedefMetni", "Durum"],
    "Durum": ["anahtar", "deger"],
}

sheets = {
    "GunlukGorevler": get_gorevler_sheet(),
    "HaftalikHedefler": get_haftalik_sheet(),
    "Durum": get_durum_sheet(),
}

rapor = "🔍 Diğer sekmelerin başlık kontrolü:\n\n"
for isim, ws in sheets.items():
    values = ws.get_all_values()
    ilk_satir = values[0] if values else []
    durum = "✅ doğru" if ilk_satir == beklenen[isim] else f"⚠️ BOZUK -> {ilk_satir}"
    rapor += f"{isim}: {durum}\n"

print(rapor)
send_message(rapor)
