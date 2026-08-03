"""GEÇİCİ KONTROL - yeni Koç tespit mekanizmalarının eşiklerine uyan
gerçek veri var mı bakar (varsa gerçek veriyle test edebiliriz)."""
from common import get_gorevler_sheet, get_aktif_rutinler

def main():
    ws = get_gorevler_sheet()
    rows = ws.get_all_records()

    print("=== Tekrarlanan görev metinleri (3+ farklı günde) ===")
    aktif_rutin_isimleri = {r["isim"].strip().lower() for r in get_aktif_rutinler()}
    metin_gunleri = {}
    for r in rows:
        metin = (r.get("GorevMetni") or "").strip()
        if not metin:
            continue
        norm = metin.lower()
        if norm in aktif_rutin_isimleri:
            continue
        metin_gunleri.setdefault(norm, set()).add(r.get("Tarih"))
    for norm, gunler in metin_gunleri.items():
        if len(gunler) >= 2:
            print(f"  '{norm}' -> {len(gunler)} gün: {sorted(gunler)}")

    print("\n=== Süresi Doldu görevler ===")
    suresi_dolanlar = [r["GorevMetni"] for r in rows if r.get("Durum") == "Süresi Doldu"]
    print(f"Toplam {len(suresi_dolanlar)} adet:")
    for m in suresi_dolanlar:
        print(" ", m)

if __name__ == "__main__":
    main()
