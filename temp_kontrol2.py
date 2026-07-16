from common import get_gorevler_sheet, bugun_str
ws = get_gorevler_sheet()
rows = ws.get_all_values()
bugun = bugun_str()
with open("kontrol2_sonuc.txt", "w", encoding="utf-8") as f:
    f.write(f"Gercek bugun: {bugun}\n\n")
    f.write("=== Son 10 satir ===\n")
    for i, row in enumerate(rows[-10:], start=len(rows)-9):
        f.write(f"{i}: {row}\n")
print("bitti")
