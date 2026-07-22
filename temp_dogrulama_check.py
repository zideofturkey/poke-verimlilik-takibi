"""GEÇİCİ DOĞRULAMA SCRIPTİ - iş bitince silinecek."""
from common import get_gorevler_sheet, get_sheet

def main():
    print("=== GunlukGorevler (son 5 satır - bogus görev eklendi mi kontrolü) ===")
    ws = get_gorevler_sheet()
    for r in ws.get_all_values()[-5:]:
        print(r)

    print("\n=== SLMLog (son 2 karar) ===")
    spreadsheet = get_sheet().spreadsheet
    slm_ws = spreadsheet.worksheet("SLMLog")
    for r in slm_ws.get_all_values()[-2:]:
        print(r[:4])  # detay (prompt) çok uzun, sadece ilk 4 kolonu göster

    print("\n=== AnlasmazlikLog (varsa) ===")
    try:
        an_ws = spreadsheet.worksheet("AnlasmazlikLog")
        rows = an_ws.get_all_values()
        print(f"Toplam {len(rows)-1} anlaşmazlık kaydı")
        for r in rows[-3:]:
            print(r)
    except Exception as e:
        print("Henüz sekme yok / okunamadı:", e)

if __name__ == "__main__":
    main()
