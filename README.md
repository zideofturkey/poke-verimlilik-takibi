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

**Rutinler vs. Günlük Görevler (önemli ayrım):**
- **Rutinler** (`common.py` içinde `RUTINLER` listesi — Fransızca, sabah/akşam telefon, verimli video) her akşam **otomatik** sorulur, kullanıcı yazmaz. Kaçırılırsa, ertesi akşam "🔁 Dünkü eksiği telafi ettim" butonu görünür.
- **Günlük görevler** kullanıcının sabah yazdığı tek seferlik işlerdir (ör. "halı saha"). Kaçırılırsa sadece **1 gün** hatırlatılır, sonra düşer — sürekli nag etmez.

## SLM Entegrasyonu — Mimari Kararı

Sistem, **yerel dil modelini (SLM) GitHub Actions'ın geçici bulut runner'ı
içinde** çalıştırır (Ollama + qwen2.5:7b), her hafta bir kez ayağa
kaldırılıp iş bitince kapatılır.

**Bu, katı anlamda "on-premise" değildir** — bilinçli bir tercih:
gerçek bir 7/24 açık yerel cihaz (laptop veya Raspberry Pi) gerektirmek,
projenin başında çözdüğümüz "laptop'tan bağımsızlık" kazanımını geri
alırdı. Sürdürülebilirlik ve otomasyon, katı on-premise tanımına sadık
kalmaktan önceliklendirildi. Model yine de açık kaynak ve küçük (SLM)
kategorisinde — sadece barındığı altyapı bulut, hesaplama bulutta
üçüncü parti bir API'ye değil, bizim kontrolümüzdeki bir runner'da
gerçekleşiyor.

## Mimari (güncel)

- `common.py` — paylaşılan Telegram/Sheets yardımcı fonksiyonları + genel görev/durum yönetimi
- `gonder.py` — proaktif mesajlar: `sabah` (serbest metin görev sorusu + telafi hatırlatması), `aksam` (bugünkü görevleri kutucuklu sorar), `pazar` (haftalık hedef), `hafta_ortasi`
- `handle_update.py` — buton basımlarını VE serbest metin cevaplarını işler (webhook tarafından anlık tetiklenir)
- `dinle.py` — webhook başarısız olursa diye saatte bir çalışan yedek (aynı işleme mantığını kullanır)
- `worker/` — Cloudflare Worker, Telegram webhook'unu GitHub Actions'a anlık iletir
- `.github/workflows/` — `gonder.yml` (zamanlama), `webhook.yml` (anlık işleme), `dinle.yml` (yedek)

**Google Sheets sekmeleri:**
- `Takip` — tüm tamamlanan/kaçırılan görevlerin log'u
- `GunlukGorevler` — her günün serbest-metinle tanımlanan görev listesi + durumu
- `HaftalikHedefler` — haftalık hedef metinleri
- `Durum` — hangi serbest-metin sorusunun cevabı bekleniyor (basit key-value)

**Veri saklama:**
- `GunlukGorevler`: 15 günden eski satırlar otomatik silinir (haftalık, Pazartesi)
- `HaftalikHedefler`: 14 günden eski satırlar otomatik silinir (bu hafta + geçen hafta yeterli)
- `Takip` (ana log): asla silinmez — uzun vadeli istatistik/streak/pattern analizi için kalıcı
- Telafi hatırlatması son 3 güne kadar geriye bakar ("dün", "2 gün önce" gibi etiketlerle)

## Durum

- [x] Telegram bot mesaj/buton akışı
- [x] Google Sheets'e loglama (doğru saat dilimi)
- [x] Zamanlanmış (GitHub Actions) tetikleme — laptop'tan bağımsız çalışma
- [x] Anlık tepki (Cloudflare Worker webhook)
- [x] Genel görev akışı: sabah serbest metin → akşam kutucuklu kontrol → telafi mantığı → haftalık hedef
- [x] Yerel SLM entegrasyonu (haftalık pattern analizi — Ollama, GitHub Actions runner'ında)
- [x] "Boşa geçen vakit" serbest-metin self-report (korelasyon analizi için veri toplama)
- [x] Günlük serbest-metin yorumlama (SLM) — "boşa vakit" cevabındaki soruları anlar, doğal bir yanıt üretir
- [x] Her an mesaj gönderme desteği — bekleyen soru olmasa bile SLM, mesajın görev ekleme mi yoksa sohbet mi olduğunu ayırt eder
- [x] Birleşik SLM sınıflandırma mimarisi — "bekleyen soru" artık katı bir kural değil, sadece AI'a bağlam ipucu; hangi kategoriye ait olduğuna (günlük görev/haftalık hedef/boşa vakit/yeni görev/sohbet) her zaman AI karar veriyor, sabit durum makinesi değil
- [x] Rutinler artık kodda değil, Sheets'te (`Rutinler` sekmesi) — kullanıcı doğrudan görüp düzenleyebilir, yeni rutin ekleyebilir, geçici durdurabilir (Aktif sütunu)
- [x] Seri/kaçırma bilgisine göre ton değişimi (kural tabanlı, AI'sız - hızlı kalması için): 5+ gündür kesintisizse kutlama, 3+ gündür kaçırılıyorsa daha dikkat çekici mesaj

## Multi-Agent Yol Haritası (sıradaki adım)

Bugüne kadarki her şey (buton akışı, SLM sınıflandırma, haftalık analiz, seri
hesaplama) gerçek bir "Koç" agent'ının üzerine oturacağı veri ve altyapıyı
hazırladı. Sıradaki adım, haftalık analizdeki bulguların **gerçek aksiyona**
dönüşmesi:
- Seviye 1 (✅ tamamlandı): mesaj/ton değişimi
- Seviye 2 (kuruluyor): Rutinler sekmesi üzerinden gerçek ayar değişikliği
  (ör. "bu rutini 2 haftadır kaçırıyorsun, hedefi küçültelim mi?")
- Seviye 3 (ileride, onaylı): zamanlama (cron) değişikliği
- [ ] Multi-agent mimarisi (Toplayıcı / Değerlendirici / Koç / Rapor)
- [ ] Observability paneli

## Güvenlik notu

`.env` ve `service_account.json` dosyaları asla repoya commit edilmemeli.
Gerçek sırlar (secrets) GitHub Actions'a taşındığında Actions Secrets
üzerinden yönetilecek.
