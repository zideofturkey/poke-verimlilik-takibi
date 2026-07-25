"""GEÇİCİ DOĞRULAMA - Süresi Doldu işaretlemesinin sonucunu gösterir."""
from common import get_gorevler_sheet, get_haftalik_sheet

def main():
    print("=== GunlukGorevler - Süresi Doldu olanlar ===")
    ws = get_gorevler_sheet()
    for r in ws.get_all_records():
        if r.get("Durum") == "Süresi Doldu":
            print(" ", r)

    print("\n=== GunlukGorevler - hâlâ Bekliyor olanlar (3 günden yeni) ===")
    for r in ws.get_all_records():
        if r.get("Durum") == "Bekliyor":
            print(" ", r)

    print("\n=== HaftalikHedefler - Süresi Doldu olanlar ===")
    ws2 = get_haftalik_sheet()
    for r in ws2.get_all_records():
        if r.get("Durum") == "Süresi Doldu":
            print(" ", r)

if __name__ == "__main__":
    main()
