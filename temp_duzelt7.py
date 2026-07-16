from common import get_haftalik_sheet, get_gorevler_sheet, bugun_str

yanlis_gorevler = [
    "11.00 Work out via Scooter",
    "2 video ile Koşullu Milyoner Varsayımları",
    "Fitcheck Geliştirmeleri (Claude MCP Denemesi, Frontend'de çok sorun var)",
    "The Bear Episode 5",
    "Poke Promotion on Chats",
]

ws_hafta = get_haftalik_sheet()
rows = ws_hafta.get_all_values()
silinecek_satirlar = []
for i, row in enumerate(rows[1:], start=2):
    if len(row) >= 2 and row[1] in yanlis_gorevler:
        silinecek_satirlar.append(i)

for satir_no in reversed(silinecek_satirlar):
    ws_hafta.delete_rows(satir_no)

ws_gorev = get_gorevler_sheet()
bugun = bugun_str()
for gorev in yanlis_gorevler:
    ws_gorev.append_row([bugun, "", gorev, "Bekliyor"])

with open("duzelt7_sonuc.txt", "w", encoding="utf-8") as f:
    f.write(f"HaftalikHedefler'den silinen satir sayisi: {len(silinecek_satirlar)}\n")
    f.write(f"GunlukGorevler'e eklenen: {len(yanlis_gorevler)}\n")
print("tamamlandi")
