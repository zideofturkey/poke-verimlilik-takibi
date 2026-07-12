"""
Ortak yardımcı fonksiyonlar - gonder.py ve dinle.py tarafından kullanılır.
Secrets ortam değişkeninden (environment variable) okunur, GitHub Actions'ta
bunlar workflow dosyası tarafından secrets'tan enjekte edilir.
"""

import os
import time
import datetime
from datetime import timezone, timedelta
import requests
import gspread
from gspread.exceptions import APIError
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials

load_dotenv()  # Yerelde .env varsa oradan okur; Actions'ta zaten env var olarak gelir

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
SHEET_ID = os.environ["SHEET_ID"]
CREDENTIALS_FILE = os.environ.get("CREDENTIALS_FILE", "service_account.json")
OFFSET_FILE = "last_update_id.txt"

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

TR_TZ = timezone(timedelta(hours=3))  # Türkiye sabit UTC+3, DST yok

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# Her gün otomatik sorulan sabit rutinler. Kullanıcı bunları sabah
# yazmaz - sistem her akşam otomatik sorar.
RUTINLER = [
    {"id": "fransizca", "isim": "Fransızca çalışma", "soru": "Bugün Fransızca çalıştın mı?"},
    {"id": "sabah_telefon", "isim": "Sabah telefon rutini", "soru": "Sabah kalkınca telefona bakmadın mı?"},
    {"id": "aksam_telefon", "isim": "Akşam telefon rutini", "soru": "Gece yatmadan telefona bakmadın mı?"},
    {"id": "verimli_video", "isim": "Verimli video izleme", "soru": "En az 1 verimli video izledin mi?"},
]


def _retry(fn, deneme=3, bekleme=3):
    """Google API'nin geçici (503 gibi) hatalarına karşı birkaç kez dener."""
    for i in range(deneme):
        try:
            return fn()
        except APIError as e:
            if i == deneme - 1:
                raise
            print(f"Google API hatası (deneme {i+1}/{deneme}), tekrar denenecek: {e}")
            time.sleep(bekleme)

_sheet_cache = None
_gorevler_cache = None
_durum_cache = None
_haftalik_cache = None


def get_gorevler_sheet():
    """Günlük görevlerin (sabah tanımlanan) tutulduğu sheet."""
    global _gorevler_cache
    if _gorevler_cache is not None:
        return _gorevler_cache
    spreadsheet = get_sheet().spreadsheet
    try:
        ws = spreadsheet.worksheet("GunlukGorevler")
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title="GunlukGorevler", rows=2000, cols=5)
        ws.append_row(["Tarih", "GorevID", "GorevMetni", "Durum"])
    _gorevler_cache = ws
    return ws


def get_durum_sheet():
    """Tek satırlık basit key-value durum tablosu (ör. hangi soruyu bekliyoruz)."""
    global _durum_cache
    if _durum_cache is not None:
        return _durum_cache
    spreadsheet = get_sheet().spreadsheet
    try:
        ws = spreadsheet.worksheet("Durum")
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title="Durum", rows=10, cols=2)
        ws.append_row(["anahtar", "deger"])
        ws.append_row(["bekleyen_soru", ""])
    _durum_cache = ws
    return ws


def get_haftalik_sheet():
    global _haftalik_cache
    if _haftalik_cache is not None:
        return _haftalik_cache
    spreadsheet = get_sheet().spreadsheet
    try:
        ws = spreadsheet.worksheet("HaftalikHedefler")
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title="HaftalikHedefler", rows=500, cols=3)
        ws.append_row(["HaftaBaslangic", "HedefMetni", "Durum"])
    _haftalik_cache = ws
    return ws


def set_bekleyen_soru(deger):
    """Hangi serbest-metin sorusunun cevabını beklediğimizi kaydeder
    (ör. 'gunluk_gorev', 'haftalik_hedef', ya da bekleme yoksa '')."""
    ws = get_durum_sheet()
    ws.update_acell("B2", deger)


def hafta_baslangic_str():
    now = datetime.datetime.now(TR_TZ)
    pazartesi = now - datetime.timedelta(days=now.weekday())
    return pazartesi.strftime("%Y-%m-%d")


SLM_MODEL = "qwen2.5:7b"
SLM_URL = "http://localhost:11434/api/generate"


def slm_sorgula(prompt, sicaklik=0.3, zaman_asimi=120):
    """Yerel Ollama modeline (GitHub Actions runner'ında geçici olarak
    ayağa kaldırılmış) bir prompt gönderir, metin cevabını döndürür."""
    resp = requests.post(
        SLM_URL,
        json={
            "model": SLM_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": sicaklik},
        },
        timeout=zaman_asimi,
    )
    resp.raise_for_status()
    return resp.json()["response"].strip()


def get_bekleyen_soru():
    ws = get_durum_sheet()
    return ws.acell("B2").value or ""


def get_sheet():
    global _sheet_cache
    if _sheet_cache is not None:
        return _sheet_cache
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)
    spreadsheet = _retry(lambda: client.open_by_key(SHEET_ID))
    try:
        worksheet = spreadsheet.worksheet("Takip")
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title="Takip", rows=1000, cols=6)
        worksheet.append_row(["Tarih", "Saat", "Görev", "Durum", "Detay"])
    _sheet_cache = worksheet
    return worksheet


def log_to_sheet(gorev, durum, detay=""):
    now = datetime.datetime.now(TR_TZ)
    get_sheet().append_row(
        [now.strftime("%Y-%m-%d"), now.strftime("%H:%M"), gorev, durum, detay]
    )
    print(f"Sheets'e yazıldı: {gorev} | {durum} | {detay}")


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
