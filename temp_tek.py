from common import get_gorevler_sheet
ws = get_gorevler_sheet()
son_satir = len(ws.get_all_values())
with open("tek_sonuc.txt", "w", encoding="utf-8") as f:
    f.write(f"Toplam satir sayisi: {son_satir}\n")
    f.write(f"Sheet basligi/adi: {ws.title}\n")
    f.write(f"Sutun sayisi (col_count): {ws.col_count}\n")
    f.write(f"Satir sayisi (row_count): {ws.row_count}\n")
print("bitti")
