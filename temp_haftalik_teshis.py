from common import get_haftalik_sheet
from panel_veri_uret import haftalik_hedef_gecmisi

ws = get_haftalik_sheet()
rows = ws.get_all_records()

with open("gecici_haftalik_teshis.txt", "w", encoding="utf-8") as f:
    f.write(f"HaftalikHedefler toplam satır: {len(rows)}\n\n")
    haftalar = sorted(set(r.get("HaftaBaslangic") for r in rows), reverse=True)
    f.write(f"Mevcut farklı HaftaBaslangic değerleri ({len(haftalar)} adet):\n")
    for h in haftalar:
        sayi = sum(1 for r in rows if r.get("HaftaBaslangic") == h)
        f.write(f"  {h}: {sayi} hedef\n")

    f.write("\n=== TÜM HAM SATIRLAR ===\n")
    for r in rows:
        f.write(f"{r}\n")

    f.write("\n=== panel_veri_uret.haftalik_hedef_gecmisi() ÇIKTISI ===\n")
    import json
    f.write(json.dumps(haftalik_hedef_gecmisi(), ensure_ascii=False, indent=2))

print("Tamamlandı.")
