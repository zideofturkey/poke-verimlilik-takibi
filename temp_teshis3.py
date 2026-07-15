from common import get_gorevler_sheet
ws = get_gorevler_sheet()
rows = ws.get_all_values()
with open("teshis3_sonuc.txt", "w", encoding="utf-8") as f:
    for i, row in enumerate(rows, start=1):
        f.write(f"{i}: {row}\n")
print("yazildi")
