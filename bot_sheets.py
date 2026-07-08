"""
Telegram bot + Google Sheets - verimlilik takip prototipi.

Akış: Telegram'da butona basarsın -> cevap Google Sheets'e yazılır.
Ayrıca script açıldıktan 60 saniye sonra proaktif bir test sorusu gönderir.

Kurulum:
    pip install requests gspread google-auth python-dotenv

Gereksinim:
    - service_account.json dosyası bu script ile aynı klasörde olmalı
    - .env dosyası (BOT_TOKEN, CHAT_ID, SHEET_ID) aynı klasörde olmalı
      (örnek için .env.example dosyasına bak)
    - Google Sheet, service account email'i ile "Editor" olarak paylaşılmış olmalı

Kullanım:
    python bot_sheets.py
"""

import time
import os
import datetime
import requests
import gspread
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials

load_dotenv()

# --- Ayarlar (artık .env dosyasından okunuyor) ---
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
SHEET_ID = os.environ["SHEET_ID"]

CREDENTIALS_FILE = "service_account.json"
OFFSET_FILE = "last_update_id.txt"

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


# --- Google Sheets bağlantısı ---
def get_sheet():
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(SHEET_ID)

    try:
        worksheet = spreadsheet.worksheet("Takip")
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title="Takip", rows=1000, cols=6)
        worksheet.append_row(["Tarih", "Saat", "Görev", "Durum", "Detay"])

    return worksheet


def log_to_sheet(gorev, durum, detay=""):
    now = datetime.datetime.now()
    sheet.append_row(
        [
            now.strftime("%Y-%m-%d"),
            now.strftime("%H:%M"),
            gorev,
            durum,
            detay,
        ]
    )
    print(f"Sheets'e yazıldı: {gorev} | {durum} | {detay}")


# --- Telegram yardımcı fonksiyonlar ---
def load_last_update_id():
    if os.path.exists(OFFSET_FILE):
        with open(OFFSET_FILE, "r") as f:
            content = f.read().strip()
            if content:
                return int(content)
    return None


def save_last_update_id(update_id):
    with open(OFFSET_FILE, "w") as f:
        f.write(str(update_id))


def send_message(text, buttons=None):
    payload = {"chat_id": CHAT_ID, "text": text}
    if buttons:
        payload["reply_markup"] = {"inline_keyboard": buttons}
    requests.post(f"{BASE_URL}/sendMessage", json=payload)


def answer_callback(callback_query_id):
    requests.post(
        f"{BASE_URL}/answerCallbackQuery",
        json={"callback_query_id": callback_query_id},
    )


def flush_backlog():
    resp = requests.get(f"{BASE_URL}/getUpdates", params={"timeout": 0})
    data = resp.json()
    results = data.get("result", [])
    if results:
        last_id = results[-1]["update_id"]
        save_last_update_id(last_id)
        print(f"Eski {len(results)} güncelleme atlandı (backlog temizlendi).")


# --- Ana döngü ---
def main():
    global sheet
    sheet = get_sheet()
    print("Google Sheets bağlantısı hazır.")

    last_update_id = load_last_update_id()
    if last_update_id is None:
        flush_backlog()
        last_update_id = load_last_update_id()

    print("Dinleme başladı... Telegram'da butona bas. (Durdurmak için Ctrl+C)")

    # --- TEST: proaktif başlatma ---
    # Script açıldıktan 60 saniye sonra KENDİLİĞİNDEN soru sorar.
    # (Gerçek sistemde bu, "her sabah 09:00'da" gibi bir zamanlayıcı olacak,
    # şimdilik hızlı test için 60 saniye.)
    proaktif_gonderildi = False
    baslangic_zamani = time.time()

    while True:
        if not proaktif_gonderildi and time.time() - baslangic_zamani > 60:
            send_message(
                "🌅 Günaydın! Bugün Fransızca çalıştın mı?",
                buttons=[
                    [
                        {"text": "Evet", "callback_data": "fransizca_evet"},
                        {"text": "Hayır", "callback_data": "fransizca_hayir"},
                    ]
                ],
            )
            print("Proaktif mesaj gönderildi (60 saniye sonra).")
            proaktif_gonderildi = True

        params = {"timeout": 30}
        if last_update_id is not None:
            params["offset"] = last_update_id + 1

        resp = requests.get(f"{BASE_URL}/getUpdates", params=params, timeout=35)
        data = resp.json()

        for update in data.get("result", []):
            last_update_id = update["update_id"]
            save_last_update_id(last_update_id)

            if "callback_query" in update:
                cq = update["callback_query"]
                callback_data = cq["data"]
                print(f"Buton basıldı: {callback_data}")

                answer_callback(cq["id"])

                if callback_data == "test_ok":
                    send_message(
                        "Bugün Fransızca çalıştın mı?",
                        buttons=[
                            [
                                {"text": "Evet", "callback_data": "fransizca_evet"},
                                {"text": "Hayır", "callback_data": "fransizca_hayir"},
                            ]
                        ],
                    )
                elif callback_data == "fransizca_evet":
                    send_message(
                        "Süper! Kaç dakika çalıştın?",
                        buttons=[
                            [
                                {"text": "5dk", "callback_data": "dk_5"},
                                {"text": "10dk", "callback_data": "dk_10"},
                                {"text": "15dk", "callback_data": "dk_15"},
                                {"text": "20dk+", "callback_data": "dk_20plus"},
                            ]
                        ],
                    )
                elif callback_data == "fransizca_hayir":
                    log_to_sheet("Fransızca", "Yapılmadı")
                    send_message("Sorun değil, yarın devam edelim 👍")
                elif callback_data.startswith("dk_"):
                    dakika = callback_data.replace("dk_", "").replace("plus", "+")
                    log_to_sheet("Fransızca", "Yapıldı", f"{dakika} dakika")
                    send_message(f"Kaydedildi: {dakika} dakika Fransızca. Tebrikler! 🎉")

        time.sleep(1)


if __name__ == "__main__":
    main()
