from common import get_gorevler_sheet, send_message

ws = get_gorevler_sheet()
rows = ws.get_all_values()
silinecek = []
for i, row in enumerate(rows[1:], start=2):
    if len(row) >= 3 and "hatırlatır mısın" in row[2]:
        silinecek.append(i)

for satir_no in reversed(silinecek):
    ws.delete_rows(satir_no)

if silinecek:
    send_message(f"✅ Yanlışlıkla eklenen {len(silinecek)} satır temizlendi.")
    print(f"{len(silinecek)} satir silindi")
else:
    print("Silinecek satir bulunamadi")
