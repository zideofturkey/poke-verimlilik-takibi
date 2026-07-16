"""
Ortak yardımcı fonksiyonlar - gonder.py ve dinle.py tarafından kullanılır.
Secrets ortam değişkeninden (environment variable) okunur, GitHub Actions'ta
bunlar workflow dosyası tarafından secrets'tan enjekte edilir.
"""

import os
import re
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
    (ör. 'gunluk_gorev', 'haftalik_hedef', ya da bekleme yoksa '').
    Ne zaman set edildiğini de kaydeder - bayat (birkaç günlük) bir
    bekleme sonsuza kadar yeni soruları engellemesin diye."""
    ws = get_durum_sheet()
    ws.update_acell("B2", deger)
    if deger:
        set_deger("bekleyen_soru_tarihi", datetime.datetime.now(TR_TZ).strftime("%Y-%m-%d"))


def hafta_baslangic_str():
    now = datetime.datetime.now(TR_TZ)
    pazartesi = now - datetime.timedelta(days=now.weekday())
    return pazartesi.strftime("%Y-%m-%d")


SLM_MODEL = "qwen2.5:3b"       # günlük sınıflandırma/cevap - hız/güvenilirlik öncelikli
SLM_MODEL_KALITELI = "qwen2.5:7b"  # haftalık analiz - kalite öncelikli, hız kritik değil
SLM_URL = "http://localhost:11434/api/generate"


def hata_logla(baglam, hata_metni):
    """Bir hata olduğunda, tahmin etmek yerine GERÇEK hatayı görebilmek
    için son_hata.txt dosyasına yazar. Bu dosya webhook.yml'in commit
    adımında otomatik olarak repoya kaydedilir."""
    try:
        with open("son_hata.txt", "w", encoding="utf-8") as f:
            f.write(f"Zaman: {datetime.datetime.now(TR_TZ).isoformat()}\n")
            f.write(f"Bağlam: {baglam}\n\n")
            f.write(hata_metni)
    except Exception as e:
        print(f"Hata loglanamadı bile: {e}")


def _ollama_hazir_mi():
    try:
        requests.get("http://localhost:11434/api/tags", timeout=2)
        return True
    except requests.exceptions.RequestException:
        return False


def _ollama_kur_ve_baslat():
    import subprocess

    # HER ZAMAN taze kurulum çalıştır (idempotent, birkaç saniye sürer).
    # Önceden "zaten kurulu mu" diye kontrol edip atlıyorduk, ama bu
    # yüzden önbellekten gelen EKSİK bir kurulum (llama-server alt
    # programı olmadan) sürekli tekrar kullanılıp duruyordu. Artık
    # programın kendisi hiç önbelleğe alınmıyor, sadece model dosyaları.
    print("Ollama kuruluyor (taze kurulum)...")
    subprocess.run(
        "curl -fsSL https://ollama.com/install.sh | sh",
        shell=True, check=True,
    )

    # install.sh bazı ortamlarda kendi arka plan servisini (systemd)
    # OTOMATİK başlatabiliyor. Biz de üstüne kendi "ollama serve"
    # sürecimizi başlatırsak port çakışması (ve muhtemelen kaynak
    # çakışması/çökme) oluyor. Önce birkaç saniye bekleyip kurulumun
    # kendisinin zaten hazır hâle gelip gelmediğine bakıyoruz.
    for _ in range(5):
        if _ollama_hazir_mi():
            print("Ollama zaten (muhtemelen kurulum sırasında otomatik) çalışıyor, kendi sürecimizi başlatmıyoruz.")
            return
        time.sleep(1)

    print("Ollama servisi başlatılıyor...")
    log_dosyasi = open("/tmp/ollama_serve.log", "w")
    subprocess.Popen(
        ["ollama", "serve"],
        stdout=log_dosyasi, stderr=log_dosyasi,
    )
    for _ in range(15):
        if _ollama_hazir_mi():
            break
        time.sleep(1)


def _slm_sorgula_tek_deneme(prompt, sicaklik, zaman_asimi, kullanilacak_model):
    import subprocess

    if not _ollama_hazir_mi():
        _ollama_kur_ve_baslat()

    print(f"Model çekiliyor (önbellekte yoksa indirir): {kullanilacak_model}")
    pull_sonuc = subprocess.run(
        ["ollama", "pull", kullanilacak_model],
        capture_output=True, text=True, timeout=180,
    )
    if pull_sonuc.returncode != 0:
        raise RuntimeError(
            f"ollama pull başarısız (kod {pull_sonuc.returncode}): "
            f"stdout={pull_sonuc.stdout[-500:]} stderr={pull_sonuc.stderr[-500:]}"
        )

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
    if resp.status_code != 200:
        raise RuntimeError(
            f"Ollama /api/generate {resp.status_code} döndü. "
            f"Cevap gövdesi: {resp.text[:1000]}"
        )
    return resp.json()["response"].strip()


def slm_sorgula(prompt, sicaklik=0.3, zaman_asimi=120, model=None):
    """Yerel Ollama modeline bir prompt gönderir, metin cevabını döndürür.
    Ollama çalışmıyorsa (ör. GitHub Actions runner'ında ilk kullanım),
    kendisi kurup başlatır - böylece bu maliyet sadece SLM'e gerçekten
    ihtiyaç duyulan anda ödenir, her serbest-metin mesajında değil.

    model: belirtilmezse hızlı (küçük) model kullanılır. Kalite öncelikli
    işler (ör. haftalık analiz) için SLM_MODEL_KALITELI verilebilir.

    Ollama'nın alt süreci (llama-server) nadiren çöküyor (ör. segfault) -
    bu durumda süreci tamamen öldürüp TAZE baştan başlatarak 1 kez daha
    dener. Çoğu geçici çökme ikinci denemede düzeliyor."""
    import subprocess

    kullanilacak_model = model or SLM_MODEL
    son_hata = None

    TOPLAM_DENEME = 3
    for deneme in range(TOPLAM_DENEME):
        try:
            return _slm_sorgula_tek_deneme(prompt, sicaklik, zaman_asimi, kullanilacak_model)
        except Exception as e:
            son_hata = e
            import traceback
            ek_bilgi = ""
            try:
                with open("/tmp/ollama_serve.log", "r", encoding="utf-8", errors="replace") as f:
                    icerik = f.read()
                    ek_bilgi = f"\n\n--- ollama serve logu (son 2000 karakter) ---\n{icerik[-2000:]}"
            except Exception:
                pass
            hata_logla(f"slm_sorgula deneme {deneme+1}/{TOPLAM_DENEME} (model={kullanilacak_model})", traceback.format_exc() + ek_bilgi)

            if deneme < TOPLAM_DENEME - 1:
                bekleme = 3 * (deneme + 1)
                print(f"Deneme {deneme+1} başarısız, Ollama'yı tamamen kapatıp {bekleme}sn sonra taze başlatarak tekrar deneniyor...")
                subprocess.run(["pkill", "-9", "-f", "ollama"], capture_output=True)
                time.sleep(bekleme)

    raise son_hata


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


def get_slm_log_sheet():
    """[MULTI-AGENT ROL: RAPOR] Sınıflandırma kararlarının ham prompt/cevap
    kaydını tutar - panelin 'SLM sınıflandırma kararları' bölümü için.
    Sadece bu fonksiyon eklendikten SONRAKİ kararlar burada olur, geçmişe
    dönük değildir."""
    spreadsheet = get_sheet().spreadsheet
    try:
        ws = spreadsheet.worksheet("SLMLog")
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title="SLMLog", rows=1000, cols=5)
        ws.update(values=[["Tarih", "Saat", "Kategori", "MesajOzet", "Detay"]], range_name="A1:E1")
    return ws


def log_slm_karari(kategori, mesaj_ozet, prompt, cevap):
    """Bir sınıflandırma kararının tam prompt+cevabını SLMLog'a ekler."""
    try:
        ws = get_slm_log_sheet()
        now = datetime.datetime.now(TR_TZ)
        detay = f"PROMPT:\n{prompt}\n\nCEVAP (ham):\n{cevap}"
        ws.append_row([
            now.strftime("%Y-%m-%d"), now.strftime("%H:%M"),
            kategori, mesaj_ozet[:80], detay[:49000],
        ])
    except Exception as e:
        print(f"SLM logu kaydedilemedi (kritik değil, devam ediliyor): {e}")


_AY_ISIMLERI = {
    "ocak": 1, "şubat": 2, "subat": 2, "mart": 3, "nisan": 4, "mayıs": 5,
    "mayis": 5, "haziran": 6, "temmuz": 7, "ağustos": 8, "agustos": 8,
    "eylül": 9, "eylul": 9, "ekim": 10, "kasım": 11, "kasim": 11,
    "aralık": 12, "aralik": 12,
}


def metinden_tarih_cikar(text):
    """Serbest metinde 'dün' ya da '15 Temmuz' gibi Türkçe bir tarih
    referansı var mı diye bakar. Bulursa YYYY-MM-DD döndürür, yoksa None
    (None = 'bugün' anlamına gelir, çağıran taraf varsayılan kullanır)."""
    metin = text.lower()
    bugun = datetime.datetime.now(TR_TZ).date()

    if re.search(r"\bdün\b", metin):
        return (bugun - datetime.timedelta(days=1)).strftime("%Y-%m-%d")

    eslesme = re.search(r"\b(\d{1,2})\s+([a-zçğıöşü]+)\b", metin)
    if eslesme:
        gun = int(eslesme.group(1))
        ay_adi = eslesme.group(2)
        if ay_adi in _AY_ISIMLERI and 1 <= gun <= 31:
            ay = _AY_ISIMLERI[ay_adi]
            yil = bugun.year
            try:
                aday_tarih = datetime.date(yil, ay, gun)
                if aday_tarih > bugun:
                    aday_tarih = datetime.date(yil - 1, ay, gun)
                return aday_tarih.strftime("%Y-%m-%d")
            except ValueError:
                pass

    return None


def guvenli_append_row(ws, degerler):
    """gspread'in append_row'u bazen (özellikle bir sekme Google Sheets'in
    'Tabloya Dönüştür' özelliğiyle bir Tabloya çevrilmişse - bkz.
    GunlukGorevler'de yaşanan gerçek olay) sessizce başarısız oluyor. Bu
    fonksiyon önce normal append_row'u dener, başarısız olursa ham Google
    Sheets API'siyle (values.append) tekrar dener - bu yöntem Tablo
    yapısıyla daha uyumlu çalışıyor (gerçek olayda doğrulandı)."""
    try:
        ws.append_row(degerler)
        return
    except Exception as e:
        print(f"append_row başarısız ({e}), ham API ile tekrar deneniyor...")

    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    gc = gspread.authorize(creds)
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/{ws.title}!A:Z:append"
    params = {"valueInputOption": "RAW", "insertDataOption": "INSERT_ROWS"}
    body = {"values": [degerler]}
    resp = gc.http_client.request("POST", url, params=params, json=body)
    if resp.status_code != 200:
        raise RuntimeError(f"Ham API de başarısız: {resp.status_code} {resp.text[:500]}")
    print("Ham API ile başarıyla eklendi.")


def get_bekleyen_soru():
    """Bekleyen soruyu döndürür - ama BAYATSA (bugünden değilse) otomatik
    olarak geçersiz sayar ve temizler. Bu, bir cevabın işlenmemesi/hata
    vermesi yüzünden sonsuza kadar takılı kalmasını önler."""
    ws = get_durum_sheet()
    deger = ws.acell("B2").value or ""
    if not deger:
        return ""
    tarih = get_deger("bekleyen_soru_tarihi")
    bugun = datetime.datetime.now(TR_TZ).strftime("%Y-%m-%d")
    if tarih and tarih != bugun:
        print(f"Bayat bekleyen_soru ('{deger}', {tarih} tarihli) bulundu, temizleniyor.")
        ws.update_acell("B2", "")
        return ""
    return deger


def update_zaten_islendi_mi(update_id):
    """dinle.py (saatlik yedek) ile anlık webhook işleyişinin AYNI update'i
    nadiren aynı anda işlemesini önler (git commit'i işlem bittikten sonra
    olduğu için git-offset kontrolü tek başına yeterli değil). Sheets
    üzerinden hızlı, anlık bir 'bu update işlendi mi' kontrolü."""
    anahtar = f"islendi_{update_id}"
    if get_deger(anahtar):
        return True
    set_deger(anahtar, "1")
    return False


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


def log_to_sheet(gorev, durum, detay="", tarih=None):
    """Aynı gün için aynı görev/rutin adına ikinci bir kayıt gelirse
    (ör. çift tıklama, ya da önce Evet sonra Hayır basılması) YENİ satır
    açmaz - var olan satırın üzerine yazar. Son basılan her zaman kazanır,
    kopya satır asla oluşmaz.

    tarih: belirtilmezse "şu an"ın tarihi kullanılır (rutinler için doğru
    olan budur). Ad-hoc görevler için, görevin KENDİ tarihi verilmeli -
    yoksa gece yarısından sonra işaretlenen bir görev, aslında ait olduğu
    günden farklı bir tarihe loglanmış olur."""
    now = datetime.datetime.now(TR_TZ)
    bugun = tarih or now.strftime("%Y-%m-%d")
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
