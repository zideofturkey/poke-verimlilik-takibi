from common import get_sheet
ws = get_sheet()
print("Worksheet basligi:", ws.title)
values = ws.get_all_values()
print("Toplam satir sayisi:", len(values))
print("Baslik satiri:", values[0] if values else "YOK")
print("Son 10 satir:")
for row in values[-10:]:
    print(row)
