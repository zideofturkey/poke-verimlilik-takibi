from common import get_gorevler_sheet

ws = get_gorevler_sheet()
rows = ws.get_all_records()
durumlar = {}
for r in rows:
    d = r.get("Durum", "")
    durumlar[d] = durumlar.get(d, 0) + 1
print("Durum dagilimi:", durumlar)

bekleyen = [r for r in rows if r.get("Durum") == "Bekliyor"]
print(f"\nBekliyor sayisi: {len(bekleyen)}")
suresi_dolmus_veya_yapilmadi = [r for r in rows if r.get("Durum") in ("Süresi Doldu", "Yapılmadı")]
print(f"Suresi Doldu + Yapilmadi sayisi (artik listede GORUNMEMELI): {len(suresi_dolmus_veya_yapilmadi)}")
for r in suresi_dolmus_veya_yapilmadi[:5]:
    print(" ", r)
