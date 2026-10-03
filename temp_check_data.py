from common import get_gorevler_sheet, get_haftalik_sheet

ws1 = get_gorevler_sheet()
rows1 = ws1.get_all_values()
print("GunlukGorevler SON 10 satir:")
for r in rows1[-10:]:
    print(r)

ws2 = get_haftalik_sheet()
rows2 = ws2.get_all_values()
print("\nHaftalikHedefler SON 10 satir:")
for r in rows2[-10:]:
    print(r)
