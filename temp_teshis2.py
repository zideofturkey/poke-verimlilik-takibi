from common import get_durum_sheet
ws = get_durum_sheet()
ws.update_acell("B2", "")
print("bekleyen_soru temizlendi (bos yapildi)")
