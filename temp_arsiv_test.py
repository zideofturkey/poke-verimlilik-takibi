"""GEÇİCİ test - arşivleme mantığını gerçek Sheets verisiyle test eder."""
import json
from common import get_gorevler_sheet, get_haftalik_sheet, get_haftalik_rutin_takip_sheet
from panel_veri_uret import (
    gunluk_gorev_arsivle,
    haftalik_hedef_arsivle,
    haftalik_rutin_takip_arsivle,
    gunluk_gorev_gecmisi,
    haftalik_hedef_gecmisi,
    haftalik_rutin_heatmap_topla,
    haftalik_rutin_oranlari_hesapla,
)

from common import get_sheet

with open("gecici_arsiv_test_sonuc.txt", "w", encoding="utf-8") as f:
    # Mevcut arşiv sekmelerinin durumunu kontrol et (önceki çalıştırmadan
    # kalma, eski anahtar şemasıyla yazılmış satırlar olabilir)
    f.write("=== MEVCUT ARŞİV SEKMELERİ DURUMU ===\n")
    spreadsheet = get_sheet().spreadsheet
    for ad in ["GunlukGorevArsiv", "HaftalikHedefArsiv", "HaftalikRutinTakipArsiv"]:
        try:
            ws = spreadsheet.worksheet(ad)
            rows = ws.get_all_values()
            f.write(f"{ad}: {len(rows)} satır (başlık dahil)\n")
        except Exception as e:
            f.write(f"{ad}: bulunamadı ({e})\n")

    f.write("\n=== GunlukGorevler GERÇEK ŞEMA KONTROLÜ ===\n")
    gorevler_rows = get_gorevler_sheet().get_all_records()
    f.write(f"Toplam satır: {len(gorevler_rows)}\n")
    if gorevler_rows:
        f.write(f"İlk satır örneği: {gorevler_rows[0]}\n")
        bos_id_sayisi = sum(1 for r in gorevler_rows if not str(r.get("GorevID", "")).strip())
        f.write(f"GorevID boş olan satır sayısı: {bos_id_sayisi}\n")

    f.write("\n=== ARŞİVLEME ÇALIŞTIRILIYOR ===\n")
    try:
        sonuc1 = gunluk_gorev_arsivle()
        f.write(f"gunluk_gorev_arsivle: {sonuc1}\n")
    except Exception as e:
        import traceback
        f.write(f"gunluk_gorev_arsivle HATA: {e}\n{traceback.format_exc()}\n")

    try:
        sonuc2 = haftalik_hedef_arsivle()
        f.write(f"haftalik_hedef_arsivle: {sonuc2}\n")
    except Exception as e:
        import traceback
        f.write(f"haftalik_hedef_arsivle HATA: {e}\n{traceback.format_exc()}\n")

    try:
        sonuc3 = haftalik_rutin_takip_arsivle()
        f.write(f"haftalik_rutin_takip_arsivle: {sonuc3}\n")
    except Exception as e:
        import traceback
        f.write(f"haftalik_rutin_takip_arsivle HATA: {e}\n{traceback.format_exc()}\n")

    f.write("\n=== 2. ÇALIŞTIRMA (idempotency testi - hiçbir şey eklenmemeli/güncellenmemeli) ===\n")
    try:
        sonuc1b = gunluk_gorev_arsivle()
        f.write(f"gunluk_gorev_arsivle (2. kez): {sonuc1b}\n")
    except Exception as e:
        f.write(f"HATA: {e}\n")

    f.write("\n=== ARŞİV SEKMELERİNİN HAM İÇERİĞİ (son durum) ===\n")
    for ad in ["GunlukGorevArsiv", "HaftalikHedefArsiv", "HaftalikRutinTakipArsiv"]:
        try:
            ws = spreadsheet.worksheet(ad)
            ham = ws.get_all_values()
            f.write(f"\n--- {ad} ({len(ham)} satır) ---\n")
            for satir in ham[:5]:
                f.write(f"{satir}\n")
            if len(ham) > 5:
                f.write(f"... ({len(ham) - 5} satır daha)\n")
        except Exception as e:
            f.write(f"{ad}: HATA {e}\n")

    f.write("\n=== ARŞİVDEN OKUMA SONUÇLARI ===\n")
    try:
        f.write("gunluk_gorev_gecmisi (ilk 2):\n")
        f.write(json.dumps(gunluk_gorev_gecmisi()[:2], ensure_ascii=False, indent=2))
    except Exception as e:
        f.write(f"HATA: {e}\n")

    try:
        f.write("\n\nhaftalik_hedef_gecmisi:\n")
        f.write(json.dumps(haftalik_hedef_gecmisi(), ensure_ascii=False, indent=2))
    except Exception as e:
        f.write(f"HATA: {e}\n")

    try:
        hrh = haftalik_rutin_heatmap_topla()
        f.write(f"\n\nhaftalik_rutin_heatmap_topla eleman sayısı: {len(hrh)}\n")
        f.write(json.dumps(hrh[-2:], ensure_ascii=False, indent=2))
    except Exception as e:
        f.write(f"HATA: {e}\n")

    try:
        hro = haftalik_rutin_oranlari_hesapla()
        f.write(f"\n\nhaftalik_rutin_oranlari_hesapla:\n")
        f.write(json.dumps(hro, ensure_ascii=False, indent=2))
    except Exception as e:
        f.write(f"HATA: {e}\n")

print("Test tamamlandı.")
