from common import get_gorevler_sheet

ws = get_gorevler_sheet()
rows = ws.get_all_values()
for i, r in enumerate(rows):
    if "Claude cop kutusu test gorevi" in str(r):
        print(f"satir_no={i+1}")
