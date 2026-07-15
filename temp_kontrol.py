from common import get_sheet
ws = get_sheet()
rows = ws.get_all_records()
beyanlar = [r for r in rows if r.get("Görev") == "Boşa geçen vakit"]
with open("kontrol_sonuc.txt", "w", encoding="utf-8") as f:
    for r in beyanlar[-5:]:
        f.write(f"{r['Tarih']} {r['Saat']} - {r.get('Detay','')}\n")
print("yazildi")
