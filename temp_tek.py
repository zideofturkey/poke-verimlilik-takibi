from common import get_haftalik_sheet, get_gorevler_sheet
ws1 = get_haftalik_sheet()
ws2 = get_gorevler_sheet()
with open("tek_sonuc.txt", "w", encoding="utf-8") as f:
    f.write("=== HaftalikHedefler ===\n")
    for i, row in enumerate(ws1.get_all_values(), start=1):
        f.write(f"{i}: {row}\n")
    f.write("\n=== GunlukGorevler (son 8 satir) ===\n")
    tum_satirlar = ws2.get_all_values()
    for i, row in enumerate(tum_satirlar[-8:], start=len(tum_satirlar)-7):
        f.write(f"{i}: {row}\n")
print("bitti")
