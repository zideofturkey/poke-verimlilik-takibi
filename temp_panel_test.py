"""GEÇİCİ test script'i - haftalık rutin panel verisini gerçek Sheets
verisiyle üretip özet çıktıyı gecici_panel_test_sonuc.txt'ye yazar.
İş bitince bu dosya ve ilgili workflow silinecek."""
import json
from panel_veri_uret import (
    haftalik_rutin_heatmap_topla,
    haftalik_rutin_oranlari_hesapla,
    get_aktif_haftalik_rutinler,
    main as panel_main,
)

with open("gecici_panel_test_sonuc.txt", "w", encoding="utf-8") as f:
    f.write("=== AKTİF HAFTALIK RUTİNLER ===\n")
    f.write(json.dumps(get_aktif_haftalik_rutinler(), ensure_ascii=False, indent=2))
    f.write("\n\n=== HAFTALIK RUTİN HEATMAP (son 12 hafta) ===\n")
    heatmap = haftalik_rutin_heatmap_topla()
    f.write(json.dumps(heatmap, ensure_ascii=False, indent=2))
    f.write("\n\n=== HAFTALIK RUTİN ORANLARI ===\n")
    oranlar = haftalik_rutin_oranlari_hesapla()
    f.write(json.dumps(oranlar, ensure_ascii=False, indent=2))

    f.write("\n\n=== main() GERÇEK AKIŞ TESTİ ===\n")
    try:
        panel_main()
        with open("panel/data.json", "r", encoding="utf-8") as df:
            data = json.load(df)
        f.write(f"main() BAŞARILI. data.json anahtarları: {list(data.keys())}\n")
        f.write(f"haftalikRutinHeatmap eleman sayısı: {len(data.get('haftalikRutinHeatmap', []))}\n")
        f.write(f"haftalikRutinOranlari: {json.dumps(data.get('haftalikRutinOranlari'), ensure_ascii=False)}\n")
        # Frontend'i gerçek veriyle test edebilmek için üretilen data.json'ı
        # AYRI bir dosya olarak da kaydediyoruz (gerçek panel/data.json'ı
        # etkilemeden - o panel_guncelle.yml'in sorumluluğunda kalıyor).
        with open("gecici_data_test.json", "w", encoding="utf-8") as gf:
            json.dump(data, gf, ensure_ascii=False, indent=2)
    except Exception as e:
        import traceback
        f.write(f"main() HATA VERDİ: {e}\n{traceback.format_exc()}\n")

print("Test tamamlandı, gecici_panel_test_sonuc.txt yazıldı.")

