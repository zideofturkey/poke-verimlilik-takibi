from common import get_haftalik_sheet, get_gorevler_sheet, bugun_str
ws_hafta = get_haftalik_sheet()
rows = ws_hafta.get_all_values()
ws_gorev = get_gorevler_sheet()
gorev_rows = ws_gorev.get_all_values()
bugun = bugun_str()

with open("teshis6_sonuc.txt", "w", encoding="utf-8") as f:
    f.write("=== HaftalikHedefler ===\n")
    for i, row in enumerate(rows, start=1):
        f.write(f"{i}: {row}\n")
    f.write("\n=== GunlukGorevler (bugun) ===\n")
    for i, row in enumerate(gorev_rows, start=1):
        if row and row[0] == bugun:
            f.write(f"{i}: {row}\n")
print("yazildi")
