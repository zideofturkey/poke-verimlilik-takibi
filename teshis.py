from common import get_sheet, send_message
ws = get_sheet()
values = ws.get_all_values()
baslik = values[0] if values else []
son_satirlar = values[-8:] if values else []

rapor = f"🔍 Teşhis:\nSekme: {ws.title}\nToplam satır: {len(values)}\nBaşlık: {baslik}\n\nSon satırlar:\n"
for row in son_satirlar:
    rapor += f"{row}\n"

print(rapor)
send_message(rapor)
