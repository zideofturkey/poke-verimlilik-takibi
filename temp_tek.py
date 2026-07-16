from common import get_gorevler_sheet, bugun_str
ws = get_gorevler_sheet()
bugun = bugun_str()
ws.append_row([bugun, "", "11.00 Work out via Scooter", "Bekliyor", ""])
with open("tek_sonuc.txt", "w") as f:
    f.write("5 sutunla eklendi")
print("bitti")
