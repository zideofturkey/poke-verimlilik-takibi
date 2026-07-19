from common import get_rutinler_sheet
ws = get_rutinler_sheet()
print(f"Mevcut sutun sayisi: {ws.col_count}")
if ws.col_count < 5:
    ws.resize(cols=5)
    print("5 sutuna buyutuldu")
ws.update_acell("E1", "TelafiEdilebilir")
with open("telafi_sonuc.txt", "w") as f:
    f.write(f"Sutun sayisi (once): oncesi, sonra genisletildi, E1 yazildi")
print("bitti")
