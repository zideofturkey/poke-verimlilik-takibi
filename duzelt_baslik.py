from common import get_gorevler_sheet, get_haftalik_sheet, get_durum_sheet, send_message

def gercekten_bos_mu(ws):
    values = ws.get_all_values()
    return not values or not any(values[0])

duzeltmeler = []

ws = get_gorevler_sheet()
if gercekten_bos_mu(ws):
    ws.update(values=[["Tarih", "GorevID", "GorevMetni", "Durum"]], range_name="A1:D1")
    duzeltmeler.append("GunlukGorevler")

ws = get_haftalik_sheet()
if gercekten_bos_mu(ws):
    ws.update(values=[["HaftaBaslangic", "HedefMetni", "Durum"]], range_name="A1:C1")
    duzeltmeler.append("HaftalikHedefler")

ws = get_durum_sheet()
if gercekten_bos_mu(ws):
    ws.update(values=[["anahtar", "deger"], ["bekleyen_soru", ""]], range_name="A1:B2")
    duzeltmeler.append("Durum")

if duzeltmeler:
    send_message(f"✅ Bu sefer gerçekten düzeltildi: {', '.join(duzeltmeler)}")
else:
    send_message("Hiçbiri boş değilmiş, garip - tekrar kontrol lazım.")

print("Tamamlandi:", duzeltmeler)
