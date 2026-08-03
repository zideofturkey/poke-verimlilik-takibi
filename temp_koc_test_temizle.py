"""GEÇİCİ - test amaçlı 'gecici_test_rutin' Koç kararı satırını Takip'ten siler."""
from common import get_sheet

ws = get_sheet()
rows = ws.get_all_values()
silinecek_satir = None
for i, row in enumerate(rows[1:], start=2):
    if len(row) > 2 and row[2] == "Koç kararı: gecici_test_rutin":
        silinecek_satir = i
        break

if silinecek_satir:
    ws.delete_rows(silinecek_satir)
    print(f"Satır {silinecek_satir} silindi.")
else:
    print("Test satırı bulunamadı (zaten temiz olabilir).")
