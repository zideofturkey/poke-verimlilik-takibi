import gspread
from google.oauth2.service_account import Credentials
import os

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_file("service_account.json", scopes=SCOPES)
gc = gspread.authorize(creds)
sheet_id = os.environ["SHEET_ID"]
service = gc.http_client

# Once test satirini sil (satir 20)
sh = gc.open_by_key(sheet_id)
ws = sh.worksheet("GunlukGorevler")
ws.delete_rows(20)

# Simdi 5 gercek gorevi ham API ile ekle
gorevler = [
    "11.00 Work out via Scooter",
    "2 video ile Koşullu Milyoner Varsayımları",
    "Fitcheck Geliştirmeleri (Claude MCP Denemesi, Frontend'de çok sorun var)",
    "The Bear Episode 5",
    "Poke Promotion on Chats",
]
bugun = "2026-07-15"
url = f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}/values/GunlukGorevler!A:D:append"
params = {"valueInputOption": "RAW", "insertDataOption": "INSERT_ROWS"}
body = {"values": [[bugun, "", g, "Bekliyor"] for g in gorevler]}
resp = service.request("POST", url, params=params, json=body)

with open("tek_sonuc.txt", "w", encoding="utf-8") as f:
    f.write(f"Test satiri silindi.\n")
    f.write(f"Status: {resp.status_code}\n")
    f.write(f"Body: {resp.text[:1000]}")
print("bitti")
