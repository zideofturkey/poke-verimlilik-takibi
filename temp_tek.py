import json as json_lib
import gspread
from google.oauth2.service_account import Credentials
import os

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_file("service_account.json", scopes=SCOPES)
gc = gspread.authorize(creds)
sheet_id = os.environ["SHEET_ID"]

# Ham Sheets API'sine dogrudan eris (gspread'in ust katmanini atla)
service = gc.http_client
url = f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}/values/GunlukGorevler!A:D:append"
params = {"valueInputOption": "RAW", "insertDataOption": "INSERT_ROWS"}
body = {"values": [["2026-07-15", "", "TEST HAM API", "Bekliyor"]]}

resp = service.request("POST", url, params=params, json=body)
with open("tek_sonuc.txt", "w", encoding="utf-8") as f:
    f.write(f"Status: {resp.status_code}\n")
    f.write(f"Body: {resp.text[:1000]}")
print("bitti")
