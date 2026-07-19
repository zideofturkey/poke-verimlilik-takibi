from common import get_rutinler_sheet
ws = get_rutinler_sheet()
ws.update(values=[["TelafiEdilebilir"]], range_name="E1")
telafi_degerleri = {
    "fransizca": "TRUE",
    "sabah_telefon": "FALSE",
    "aksam_telefon": "FALSE",
    "verimli_video": "TRUE",
    "mewing": "TRUE",
}
rows = ws.get_all_values()
for i, row in enumerate(rows[1:], start=2):
    rutin_id = row[0]
    deger = telafi_degerleri.get(rutin_id, "TRUE")
    ws.update(values=[[deger]], range_name=f"E{i}")
print("tamamlandi")
