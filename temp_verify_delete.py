from common import get_gorevler_sheet, get_sheet

ws = get_gorevler_sheet()
rows = ws.get_all_values()
bulundu = False
for i, r in enumerate(rows):
    if "Claude test gorevi silme ornegi" in str(r):
        print(f"HALA VAR: satir {i+1}: {r}")
        bulundu = True
if not bulundu:
    print("SILINMIS - satir artik yok, basarili.")

ws2 = get_sheet().spreadsheet.worksheet("SLMLog")
rows2 = ws2.get_all_values()
print("\nSON SATIR (siniflandirma):")
print(rows2[-1][:4])
