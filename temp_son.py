import gspread
from google.oauth2.service_account import Credentials
import os

SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_file("service_account.json", scopes=SCOPES)
gc = gspread.authorize(creds)
sheet_id = os.environ["SHEET_ID"]
sh = gc.open_by_key(sheet_id)

ws_hafta = sh.worksheet("HaftalikHedefler")
rows = ws_hafta.get_all_values()

with open("son_sonuc.txt", "w", encoding="utf-8") as f:
    f.write("=== HaftalikHedefler (mevcut) ===\n")
    for i, row in enumerate(rows, start=1):
        f.write(f"{i}: {row}\n")

yanlis_metinler = [
    "13.00 Work out via Scooter",
    "2 video ile Koşullu Milyoner Varsayımları",
    "Fitcheck Geliştirmeleri (Claude MCP Denemesi, Frontend'de çok sorun var)",
    "The Bear Episode 5",
    "Poke Promotion on Chats",
]
silinecek = [i for i, row in enumerate(rows, start=1) if len(row) >= 2 and row[1] in yanlis_metinler]

for satir_no in sorted(silinecek, reverse=True):
    ws_hafta.delete_rows(satir_no)

with open("son_sonuc.txt", "a", encoding="utf-8") as f:
    f.write(f"\nSilinen satirlar: {silinecek}\n")

# Ham API ile GunlukGorevler'e ekle
service = gc.http_client
bugun = "2026-07-16"
url = f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}/values/GunlukGorevler!A:D:append"
params = {"valueInputOption": "RAW", "insertDataOption": "INSERT_ROWS"}
body = {"values": [[bugun, "", g, "Bekliyor"] for g in yanlis_metinler]}
resp = service.request("POST", url, params=params, json=body)

with open("son_sonuc.txt", "a", encoding="utf-8") as f:
    f.write(f"\nEkleme status: {resp.status_code}\n")
    f.write(f"Body: {resp.text[:500]}\n")
print("bitti")
