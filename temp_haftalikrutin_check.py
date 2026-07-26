"""GEÇİCİ DOĞRULAMA."""
from common import get_sheet, get_aktif_haftalik_rutinler, get_haftalik_rutin_takip_sheet, hafta_baslangic_str

def main():
    spreadsheet = get_sheet().spreadsheet
    ws = spreadsheet.worksheet("SLMLog")
    print("=== SLMLog (son karar) ===")
    for r in ws.get_all_values()[-1:]:
        print(r[:4])

    print("\n=== Haftalık rutinler ve bu haftaki durumları ===")
    print("Aktif haftalık rutinler:", get_aktif_haftalik_rutinler())
    ws2 = get_haftalik_rutin_takip_sheet()
    hafta = hafta_baslangic_str()
    print(f"Bu hafta ({hafta}) için takip kayıtları:")
    for r in ws2.get_all_records():
        if r.get("HaftaBaslangic") == hafta:
            print(" ", r)

if __name__ == "__main__":
    main()
