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


def get_deger(anahtar, varsayilan=""):
    """Durum sekmesinden genel amaçlı bir anahtar-değer okur (ör. 'sabah
    en son ne zaman çalıştı' gibi bekçi/watchdog kontrolleri için)."""
    ws = get_durum_sheet()
    rows = ws.get_all_records()
    for r in rows:
        if r.get("anahtar") == anahtar:
            return r.get("deger", varsayilan)
    return varsayilan


def set_deger(anahtar, deger):
    ws = get_durum_sheet()
    values = ws.get_all_values()
    for i, row in enumerate(values[1:], start=2):
        if row and row[0] == anahtar:
            ws.update_cell(i, 2, deger)
            return
    ws.append_row([anahtar, deger])


def set_bekleyen_soru(deger):
    """Hangi serbest-metin sorusunun cevabını beklediğimizi kaydeder
    (ör. 'gunluk_gorev', 'haftalik_hedef', ya da bekleme yoksa '')."""
    ws = get_durum_sheet()
    ws.update_acell("B2", deger)


def hafta_baslangic_str():
    now = datetime.datetime.now(TR_TZ)
    pazartesi = now - datetime.timedelta(days=now.weekday())
    return pazartesi.strftime("%Y-%m-%d")


SLM_MODEL = "qwen2.5:3b"       # günlük sınıflandırma/cevap - hız/güvenilirlik öncelikli
SLM_MODEL_KALITELI = "qwen2.5:7b"  # haftalık analiz - kalite öncelikli, hız kritik değil
SLM_URL = "http://localhost:11434/api/generate"


def _ollama_hazir_mi():
    try:
        requests.get("http://localhost:11434/api/tags", timeout=2)
        return True
    except requests.exceptions.RequestException:
        return False


def _ollama_kur_ve_baslat():
    import subprocess
    import shutil

    if shutil.which("ollama") is None:
        print("Ollama kuruluyor...")
        subprocess.run(
            "curl -fsSL https://ollama.com/install.sh | sh",
            shell=True, check=True,
        )

    print("Ollama servisi başlatılıyor...")
    subprocess.Popen(
        ["ollama", "serve"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    for _ in range(15):
        if _ollama_hazir_mi():
            break
        time.sleep(1)


def slm_sorgula(prompt, sicaklik=0.3, zaman_asimi=120, model=None):
    """Yerel Ollama modeline bir prompt gönderir, metin cevabını döndürür.
    Ollama çalışmıyorsa (ör. GitHub Actions runner'ında ilk kullanım),
    kendisi kurup başlatır - böylece bu maliyet sadece SLM'e gerçekten
    ihtiyaç duyulan anda ödenir, her serbest-metin mesajında değil.

    model: belirtilmezse hızlı (küçük) model kullanılır. Kalite öncelikli
    işler (ör. haftalık analiz) için SLM_MODEL_KALITELI verilebilir."""
    kullanilacak_model = model or SLM_MODEL

    if not _ollama_hazir_mi():
        _ollama_kur_ve_baslat()

    print(f"Model çekiliyor (önbellekte yoksa indirir): {kullanilacak_model}")
    import subprocess
    subprocess.run(["ollama", "pull", kullanilacak_model], check=True)

    resp = requests.post(
        SLM_URL,
        json={
            "model": kullanilacak_model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": sicaklik},
        },
        timeout=zaman_asimi,
    )
    resp.raise_for_status()
    return resp.json()["response"].strip()


# Sheets'e taşınmadan önceki varsayılanlar - sadece ilk kurulumda
# (sekme boşsa) Rutinler sekmesini doldurmak için kullanılır.
_VARSAYILAN_RUTINLER = [
    {"id": "fransizca", "isim": "Fransızca çalışma", "soru": "Bugün Fransızca çalıştın mı?"},
    {"id": "sabah_telefon", "isim": "Sabah telefon rutini", "soru": "Sabah kalkınca telefona bakmadın mı?"},
    {"id": "aksam_telefon", "isim": "Akşam telefon rutini", "soru": "Gece yatmadan telefona bakmadın mı?"},
    {"id": "verimli_video", "isim": "Verimli video izleme", "soru": "En az 1 verimli video izledin mi?"},
]

_rutinler_cache = None


def get_rutinler_sheet():
    global _rutinler_cache
    if _rutinler_cache is not None:
        return _rutinler_cache
    spreadsheet = get_sheet().spreadsheet
    try:
        ws = spreadsheet.worksheet("Rutinler")
        if not ws.get_all_values() or not any(ws.get_all_values()[0]):
            raise gspread.WorksheetNotFound  # var ama boş - yeniden doldur
    except gspread.WorksheetNotFound:
        try:
            ws = spreadsheet.worksheet("Rutinler")
        except gspread.WorksheetNotFound:
            ws = spreadsheet.add_worksheet(title="Rutinler", rows=50, cols=4)
        ws.update(values=[["RutinID", "Isim", "Soru", "Aktif"]], range_name="A1:D1")
        for r in _VARSAYILAN_RUTINLER:
            ws.append_row([r["id"], r["isim"], r["soru"], "TRUE"])
    _rutinler_cache = ws
    return ws


def get_aktif_rutinler():
    """Rutinler sekmesinden Aktif=TRUE olan satırları döndürür.
    Kullanıcı bu sekmeyi Sheets'ten doğrudan düzenleyebilir (yeni rutin
    ekleme, soru metnini değiştirme, geçici olarak durdurma)."""
    ws = get_rutinler_sheet()
    rows = ws.get_all_records()
    return [
        {"id": r["RutinID"], "isim": r["Isim"], "soru": r["Soru"]}
        for r in rows
        if str(r.get("Aktif", "TRUE")).strip().upper() != "FALSE"
    ]


def rutin_serisi_hesapla(rutin_isim):
    """[MULTI-AGENT ROL: DEĞERLENDİRİCİ] Bu fonksiyon Değerlendirici
    agent'ının çekirdeği - ham veriyi (Takip) örüntüye (seri/kaçırma)
    çevirir. gonder.py (Toplayıcı) ve analiz.py (Koç) bu fonksiyonu çağırır.

    Dünden geriye doğru gidip kaç gündür kesintisiz yapıldığını
    (streak) ya da kaç gündür kesintisiz kaçırıldığını (miss_streak)
    hesaplar. 'Telafi' durumu nötr bir sıfırlama noktasıdır - ne seriyi
    uzatır (tam kaliteli tamamlama değil) ne de kaçırma sayılır (bir şey
    yapılmıştır) - o günde durma noktası olur."""
    ws = get_sheet()
    rows = ws.get_all_records()
    gunluk_durum = {}
    for r in rows:
        if r.get("Görev") != rutin_isim:
            continue
        try:
            tarih = datetime.datetime.strptime(r["Tarih"], "%Y-%m-%d").date()
        except (ValueError, KeyError):
            continue
        gunluk_durum[tarih] = r.get("Durum")

    bugun = datetime.datetime.now(TR_TZ).date()
    streak = 0
    miss_streak = 0
    gun = bugun - datetime.timedelta(days=1)
    while True:
        durum = gunluk_durum.get(gun)
        if durum is None:
            break
        if durum == "Telafi":
            break  # nötr durak noktası - ne uzat ne kaçırma say
        if durum == "Yapıldı":
            if miss_streak > 0:
                break
            streak += 1
        else:  # "Yapılmadı"
            if streak > 0:
                break
            miss_streak += 1
        gun -= datetime.timedelta(days=1)
    return streak, miss_streak


def turkce_disi_karakter_var_mi(metin):
    """Çince, Arapça, Kiril vb. beklenmedik alfabelerden karakter olup
    olmadığını kontrol eder - model 'dil kayması' yaşarsa yakalamak için."""
    for ch in metin:
        kod = ord(ch)
        if kod > 0x2FF and kod not in (0x2018, 0x2019, 0x201C, 0x201D, 0x2026):
            return True
    return False


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
    """Aynı gün için aynı görev/rutin adına ikinci bir kayıt gelirse
    (ör. çift tıklama, ya da önce Evet sonra Hayır basılması) YENİ satır
    açmaz - var olan satırın üzerine yazar. Son basılan her zaman kazanır,
    kopya satır asla oluşmaz."""
    now = datetime.datetime.now(TR_TZ)
    bugun = now.strftime("%Y-%m-%d")
    saat = now.strftime("%H:%M")

    ws = get_sheet()
    rows = ws.get_all_values()
    for i, row in enumerate(rows[1:], start=2):
        if len(row) >= 3 and row[0] == bugun and row[2] == gorev:
            ws.update(values=[[bugun, saat, gorev, durum, detay]], range_name=f"A{i}:E{i}")
            print(f"Sheets'te güncellendi (üzerine yazıldı): {gorev} | {durum} | {detay}")
            return

    ws.append_row([bugun, saat, gorev, durum, detay])
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
