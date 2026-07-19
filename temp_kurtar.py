import gspread
from google.oauth2.service_account import Credentials
import os

SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_file("service_account.json", scopes=SCOPES)
gc = gspread.authorize(creds)
sheet_id = os.environ["SHEET_ID"]
service = gc.http_client

bugun = "2026-07-19"
gorevler = [
    "prendre une douche détaillée",
    "une film - av mevsimi",
    "cleaning the room",
    "poke improvements",
    "portföy takip dosyası düzenlemesi",
]

url = f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}/values/GunlukGorevler!A:D:append"
params = {"valueInputOption": "RAW", "insertDataOption": "INSERT_ROWS"}
body = {"values": [[bugun, "", g, "Bekliyor"] for g in gorevler]}
resp = service.request("POST", url, params=params, json=body)

with open("kurtar_sonuc.txt", "w", encoding="utf-8") as f:
    f.write(f"Status: {resp.status_code}\n{resp.text[:500]}")
print("bitti")
