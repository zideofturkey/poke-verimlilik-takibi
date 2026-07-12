from common import get_gorevler_sheet, send_message

ws = get_gorevler_sheet()
mevcut = ws.cell(8, 3).value
if mevcut and "travaille" in mevcut and "ekliyorum" in mevcut:
    ws.update_cell(8, 3, "travaille bien français")
    send_message("✅ C8'deki görev metni düzeltildi.")
    print("Duzeltildi")
else:
    print(f"Beklenen icerik bulunamadi: {mevcut!r}")
