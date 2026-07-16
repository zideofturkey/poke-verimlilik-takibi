import gspread
from google.oauth2.service_account import Credentials
import os

SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_file("service_account.json", scopes=SCOPES)
gc = gspread.authorize(creds)
sh = gc.open_by_key(os.environ["SHEET_ID"])
ws = sh.worksheet("GunlukGorevler")
rows = ws.get_all_values()

with open("basit_sonuc.txt", "w", encoding="utf-8") as f:
    f.write(f"Toplam satir: {len(rows)}\n\n")
    for i, row in enumerate(rows[-12:], start=len(rows)-11):
        f.write(f"{i}: {row}\n")
print("bitti")
