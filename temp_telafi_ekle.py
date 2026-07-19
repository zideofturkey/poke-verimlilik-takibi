import gspread
from google.oauth2.service_account import Credentials
import os

SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_file("service_account.json", scopes=SCOPES)
gc = gspread.authorize(creds)
sheet_id = os.environ["SHEET_ID"]
service = gc.http_client

telafi_degerleri = {
    "fransizca": "TRUE",
    "sabah_telefon": "FALSE",
    "aksam_telefon": "FALSE",
    "verimli_video": "TRUE",
    "mewing": "TRUE",
}

# Ham API ile tek seferde tum E sutununu yaz (E1 basliktan E6'ya kadar)
degerler = [["TelafiEdilebilir"]]
sira = ["fransizca", "sabah_telefon", "aksam_telefon", "verimli_video", "mewing"]
for rid in sira:
    degerler.append([telafi_degerleri[rid]])

url = f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}/values/Rutinler!E1:E6"
params = {"valueInputOption": "RAW"}
body = {"values": degerler}
resp = service.request("PUT", url, params=params, json=body)

with open("telafi_sonuc.txt", "w", encoding="utf-8") as f:
    f.write(f"Status: {resp.status_code}\n")
    f.write(f"Body: {resp.text[:500]}")
print("bitti")
