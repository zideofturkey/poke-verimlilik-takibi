from common import get_gorevler_sheet, get_haftalik_sheet, get_durum_sheet, send_message

duzeltmeler = []

ws = get_gorevler_sheet()
if not ws.get_all_values():
    ws.append_row(["Tarih", "GorevID", "GorevMetni", "Durum"])
    duzeltmeler.append("GunlukGorevler")

ws = get_haftalik_sheet()
if not ws.get_all_values():
    ws.append_row(["HaftaBaslangic", "HedefMetni", "Durum"])
    duzeltmeler.append("HaftalikHedefler")

ws = get_durum_sheet()
if not ws.get_all_values():
    ws.append_row(["anahtar", "deger"])
    ws.append_row(["bekleyen_soru", ""])
    duzeltmeler.append("Durum")

if duzeltmeler:
    send_message(f"✅ Başlıkları geri eklendi: {', '.join(duzeltmeler)}")
else:
    send_message("Tüm sekmeler zaten doğru, düzeltmeye gerek yoktu.")

print("Tamamlandi:", duzeltmeler)
