from common import get_rutinler_sheet
ws = get_rutinler_sheet()
ws.update_acell("E1", "TelafiEdilebilir")
with open("telafi_sonuc.txt", "w") as f:
    f.write("E1 yazildi")
print("bitti")
