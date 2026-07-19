import gspread
from google.oauth2.service_account import Credentials
import os
import datetime
import zoneinfo

TR_TZ = zoneinfo.ZoneInfo("Europe/Istanbul")
bugun = datetime.datetime.now(TR_TZ).strftime("%Y-%m-%d")

SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_file("service_account.json", scopes=SCOPES)
gc = gspread.authorize(creds)
sheet_id = os.environ["SHEET_ID"]
sh = gc.open_by_key(sheet_id)

ws_hafta = sh.worksheet("HaftalikHedefler")
rows = ws_hafta.get_all_values()
silinecek = [i for i, row in enumerate(rows, start=1)
             if len(row) >= 2 and row[1] in ("günlük görevlere ekleme yap:", "portföy takip dosyası düzenlemesi")]
for satir_no in sorted(silinecek, reverse=True):
    ws_hafta.delete_rows(satir_no)

service = gc.http_client
url = f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}/values/GunlukGorevler!A:D:append"
params = {"valueInputOption": "RAW", "insertDataOption": "INSERT_ROWS"}
body = {"values": [[bugun, "", "portföy takip dosyası düzenlemesi", "Bekliyor"]]}
resp = service.request("POST", url, params=params, json=body)

with open("duzelt9_sonuc.txt", "w", encoding="utf-8") as f:
    f.write(f"Gercek bugun: {bugun}\n")
    f.write(f"Silinen satirlar (HaftalikHedefler): {silinecek}\n")
    f.write(f"Ekleme status: {resp.status_code}\n{resp.text[:300]}")
print("bitti")
