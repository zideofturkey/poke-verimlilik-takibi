from common import get_gorevler_sheet

ws = get_gorevler_sheet()
rows = ws.get_all_values()
for i, r in enumerate(rows):
    if len(r) > 2 and "TEST - Claude dogrulama satiri" in r[2]:
        print(f"Siliniyor: satir {i+1} -> {r}")
        ws.delete_rows(i + 1)
        break
else:
    print("Bulunamadi - zaten silinmis olabilir")
