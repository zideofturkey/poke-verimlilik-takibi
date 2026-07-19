from common import get_rutinler_sheet
ws = get_rutinler_sheet()
rows = ws.get_all_values()
with open("rutin_oku_sonuc.txt", "w", encoding="utf-8") as f:
    for i, row in enumerate(rows, start=1):
        f.write(f"{i}: {row}\n")
print("bitti")
