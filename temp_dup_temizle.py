from common import get_sheet, send_message

ws = get_sheet()
rows = ws.get_all_values()
gorulen = {}
silinecek = []
for i, row in enumerate(rows[1:], start=2):
    if len(row) < 3:
        continue
    anahtar = (row[0], row[2])  # (tarih, gorev)
    if anahtar in gorulen:
        silinecek.append(i)  # ikinci (daha sonraki) kaydi sil, ilkini birak
    else:
        gorulen[anahtar] = i

for satir_no in reversed(silinecek):
    ws.delete_rows(satir_no)

if silinecek:
    send_message(f"✅ {len(silinecek)} kopya satır temizlendi.")
    print(f"{len(silinecek)} kopya silindi")
else:
    print("Kopya bulunamadi")
