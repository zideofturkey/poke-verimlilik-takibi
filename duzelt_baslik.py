from common import get_sheet, send_message

ws = get_sheet()
values = ws.get_all_values()

beklenen_baslik = ["Tarih", "Saat", "Görev", "Durum", "Detay"]

if values and values[0] == beklenen_baslik:
    send_message("Başlık zaten doğru, düzeltmeye gerek yok.")
else:
    ws.insert_row(beklenen_baslik, 1)
    send_message(f"✅ Başlık satırı geri eklendi: {beklenen_baslik}")

print("Islem tamamlandi")
