from common import get_haftalik_rutin_takip_sheet, hafta_baslangic_str
import datetime

ws = get_haftalik_rutin_takip_sheet()
rows = ws.get_all_values()
print("Bu hafta:", hafta_baslangic_str())
print("TUM SATIRLAR:")
for i, r in enumerate(rows):
    print(f"satir {i+1}: {r}")
