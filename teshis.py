from common import get_gorevler_sheet, get_haftalik_sheet, get_durum_sheet, send_message

sheets = {
    "GunlukGorevler": get_gorevler_sheet(),
    "HaftalikHedefler": get_haftalik_sheet(),
    "Durum": get_durum_sheet(),
}

rapor = "🔍 Ham içerik kontrolü:\n\n"
for isim, ws in sheets.items():
    values = ws.get_all_values()
    rapor += f"--- {isim} ---\n"
    rapor += f"Satır sayısı: {len(values)}\n"
    for i, row in enumerate(values[:5]):
        rapor += f"  [{i}] {row!r}\n"
    rapor += "\n"

print(rapor)
send_message(rapor)
