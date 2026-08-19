from common import get_haftalik_sheet, get_haftalik_rutin_takip_sheet, hafta_baslangic_str
import datetime

bu_hafta = datetime.datetime.strptime(hafta_baslangic_str(), "%Y-%m-%d").date()
gecen_hafta = (bu_hafta - datetime.timedelta(days=7)).strftime("%Y-%m-%d")
print("Bu hafta:", bu_hafta, "| Gecen hafta:", gecen_hafta)

ws1 = get_haftalik_sheet()
print("\nHaftalikHedefler - gecen hafta satirlari:")
for r in ws1.get_all_values()[1:]:
    if r and r[0] == gecen_hafta:
        print(r)

ws2 = get_haftalik_rutin_takip_sheet()
print("\nHaftalikRutinTakip - gecen hafta satirlari:")
for r in ws2.get_all_values()[1:]:
    if r and r[0] == gecen_hafta:
        print(r)
