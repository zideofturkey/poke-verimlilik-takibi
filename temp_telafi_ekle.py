from common import get_rutinler_sheet
import time
ws = get_rutinler_sheet()
telafi_degerleri = {
    "fransizca": "TRUE",
    "sabah_telefon": "FALSE",
    "aksam_telefon": "FALSE",
    "verimli_video": "TRUE",
    "mewing": "TRUE",
}
rows = ws.get_all_values()
sonuc = []
for i, row in enumerate(rows[1:], start=2):
    rutin_id = row[0]
    deger = telafi_degerleri.get(rutin_id, "TRUE")
    ws.update_acell(f"E{i}", deger)
    sonuc.append(f"E{i} ({rutin_id}) = {deger}")
    time.sleep(2)
with open("telafi_sonuc.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(sonuc))
print("bitti")
