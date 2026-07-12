from common import get_gorevler_sheet, send_message

ws = get_gorevler_sheet()
# C7 hucresi: bozuk (Cince karakterli) gorev metni
mevcut = ws.cell(7, 3).value
if mevcut and "评估" in mevcut:
    ws.update_cell(7, 3, "Watch at least 2 stock market evaluation videos")
    send_message("✅ Bozuk görev metni düzeltildi.")
    print("Duzeltildi")
else:
    print(f"Beklenen icerik bulunamadi, mevcut: {mevcut!r}")
