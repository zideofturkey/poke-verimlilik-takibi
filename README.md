# poke-verimlilik-takibi

Kişisel verimlilik/rutin takip sistemi. Telegram bot üzerinden buton bazlı
soru-cevap ile günlük/haftalık hedefleri takip eder, cevapları Google
Sheets'e kaydeder.

## Kurulum

1. Bağımlılıkları kur:
   ```
   pip install requests gspread google-auth python-dotenv
   ```

2. `.env.example` dosyasını `.env` olarak kopyala ve kendi değerlerini gir:
   ```
   BOT_TOKEN=...
   CHAT_ID=...
   SHEET_ID=...
   ```

3. Google Cloud service account JSON dosyanı `service_account.json` adıyla
   bu klasöre koy (bu dosya asla commit'lenmez, `.gitignore`'da).

4. Çalıştır:
   ```
   python bot_sheets.py
   ```

## Mimari (güncel)

- `common.py` — paylaşılan Telegram/Sheets yardımcı fonksiyonları
- `gonder.py` — proaktif mesaj gönderir (sabah/hafta ortası/pazar), GitHub Actions tarafından zamanlanır
- `dinle.py` — buton basımlarını kontrol eder, işler, Sheets'e yazar; her 5 dakikada bir Actions tarafından tetiklenir
- `bot_sheets.py` — yerel geliştirme/test için sürekli-açık (polling) versiyon, artık üretimde kullanılmıyor
- `.github/workflows/gonder.yml` ve `dinle.yml` — zamanlama, laptop'tan tamamen bağımsız çalışır

Tüm secrets (`BOT_TOKEN`, `CHAT_ID`, `SHEET_ID`, `GOOGLE_SERVICE_ACCOUNT_JSON`)
GitHub Actions Secrets üzerinden yönetiliyor, kodda hiçbir yerde açık yazılı değil.

## Durum

- [x] Telegram bot mesaj/buton akışı
- [x] Google Sheets'e loglama
- [x] Zamanlanmış (GitHub Actions) tetikleme — laptop'tan bağımsız çalışma
- [ ] Yerel SLM entegrasyonu (karar/analiz katmanı)
- [ ] Multi-agent mimarisi (Toplayıcı / Değerlendirici / Koç / Rapor)
- [ ] Observability paneli

## Güvenlik notu

`.env` ve `service_account.json` dosyaları asla repoya commit edilmemeli.
Gerçek sırlar (secrets) GitHub Actions'a taşındığında Actions Secrets
üzerinden yönetilecek.
