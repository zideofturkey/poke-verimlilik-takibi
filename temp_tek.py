from common import get_gorevler_sheet, bugun_str
ws = get_gorevler_sheet()
bugun = bugun_str()
degerler = ws.get_all_values()
son_satir = len(degerler)
yeni_satir_no = son_satir + 1
ws.update(values=[[bugun, "", "11.00 Work out via Scooter", "Bekliyor"]], range_name=f"A{yeni_satir_no}:D{yeni_satir_no}")
with open("tek_sonuc.txt", "w") as f:
    f.write(f"Satir {yeni_satir_no}'e dogrudan yazildi")
print("bitti")
