from common import get_haftalik_sheet
ws = get_haftalik_sheet()
ws.delete_rows(9)
with open("tek_sonuc.txt", "w") as f:
    f.write("satir 9 silindi")
print("bitti")
