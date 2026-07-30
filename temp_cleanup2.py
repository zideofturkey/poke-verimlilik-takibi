from common import get_haftalik_sheet

ws = get_haftalik_sheet()
rows = ws.get_all_values()
for i, r in enumerate(rows):
    if len(r) > 1 and "TEST2 - Claude dogrulama" in r[1]:
        print(f"Siliniyor: satir {i+1} -> {r}")
        ws.delete_rows(i + 1)
        break
else:
    print("Bulunamadi")
