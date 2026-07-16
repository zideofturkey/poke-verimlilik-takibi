from common import get_haftalik_sheet
ws = get_haftalik_sheet()
ws.delete_rows(11)
with open("tek_sonuc.txt", "w") as f:
    f.write("satir 11 silindi")
print("bitti")
