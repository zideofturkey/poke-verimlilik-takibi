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
- [x] Birleşik SLM sınıflandırma mimarisi — "bekleyen soru" artık katı bir kural değil, sadece AI'a bağlam ipucu; hangi kategoriye ait olduğuna (günlük görev/haftalık hedef/boşa vakit/yeni görev/**rutin tamamlama**/sorgu/sohbet) her zaman AI karar veriyor, sabit durum makinesi değil. Sorgu cevapları artık **deterministik** (SLM'e yazdırılmıyor) — direkt, doğru Türkçe liste formatında, sadece bugünün verisini kapsıyor. "Fransızca rutinimi tamamladım" gibi cümleler otomatik olarak ilgili rutini işaretliyor.
- [x] Periyodik hatırlatma: rutinler günde 3 kez tetiklenebilir (13:00, 17:00, 21:00) ama HER SEFERİNDE sadece o gün için henüz cevaplanmamış rutinler sorulur — zaten cevaplanmışsa mesaj bile gelmez (sessiz kalır, spam yapmaz)
- [x] Bekçi (watchdog) mekanizması — GitHub Actions'ın zamanlanmış tetiklemeyi bazen atlaması (drop etmesi) ihtimaline karşı, öğle/akşamüstü/akşam kontrollerinden önce "sabah mesajı bugün gerçekten gitti mi" diye kontrol edilir, gitmediyse otomatik olarak gönderilir
- [x] SLM güvenilirlik düzeltmesi: günlük sınıflandırma/cevaplar artık daha küçük/hızlı model (qwen2.5:3b) kullanıyor (büyük modelin soğuk-başlangıç süresi zaman zaman zaman aşımına uğruyordu), haftalık analiz + Koç önerileri kalite öncelikli büyük modelde (qwen2.5:7b) kalıyor. Ollama'nın kendi kurulumu da artık önbelleğe alınıyor (önceden sadece model önbelleğe alınıyordu).
- [x] Üçüncü durum: "Telafi" — dünkü kaçırmayı bugün telafi etmek, ne tam zamanında yapmış (Yapıldı) ne de hiç yapmamış (Yapılmadı) gibi sayılmaz; ayrı, nötr bir kategori. Seri (streak) hesabında nötr durak noktası, panelde ayrı bir rozetle (🔁, amber renk), haftalık analizde ayrı bir istatistik olarak gösteriliyor.
- [x] Rutinler artık kodda değil, Sheets'te (`Rutinler` sekmesi) — kullanıcı doğrudan görüp düzenleyebilir, yeni rutin ekleyebilir, geçici durdurabilir (Aktif sütunu)
- [x] Seri/kaçırma bilgisine göre ton değişimi (kural tabanlı, AI'sız - hızlı kalması için): 5+ gündür kesintisizse kutlama, 3+ gündür kaçırılıyorsa daha dikkat çekici mesaj

## Multi-Agent Mimarisi (dürüst not)

Sistem, **kavramsal/mantıksal olarak** 4 role ayrılmış tek bir koordineli
pipeline'dır — Ali Bey'in tanımındaki "birbiriyle konuşan, iş bölümü yapan
bağımsız ajanlar" anlamında **gerçek anlamda ayrı, bağımsız çalışan 4 ajan
değildir.** Bu bilinçli bir tercih: bağımsız ajanlar (her biri kendi
zamanlamasıyla, birbirinden habersiz çalışan) burada koordinasyon
sorunlarını (ör. aynı veriye eşzamanlı yazma, "bu zaten yapıldı mı"
kontrolünün tutarsızlaşması) azaltmaz, artırırdı — zaten yaşadığımız
gerçek hataların çoğu (çift mesaj, git çakışması) tam da koordinasyon
eksikliğinden kaynaklanmıştı. Tek kullanıcılı, tek paylaşılan veri
kaynaklı (Google Sheets) bir sistemde asıl değer ayrışmadan değil,
**sıkı koordinasyon ve tek doğruluk kaynağından (single source of
truth)** geliyor.

Yine de bu 4 rol ayrımı **gerçek ve faydalı** — kodun hangi parçasının
hangi sorumluluğu taşıdığını netleştiriyor, blackboard deseniyle (ortak
Sheets üzerinden dolaylı haberleşme) tutarlı, ve ileride gerçekten
bağımsız ajanlara bölünmesi gerekirse (ör. çok kullanıcılı bir sisteme
büyürse) bu ayrım zaten hazır bir temel oluşturuyor.

```
Telegram → Toplayıcı → [Ortak Hafıza: Google Sheets] → Değerlendirici, Koç, Rapor
```

| Agent | Kod karşılığı | Sorumluluğu |
|---|---|---|
| **Toplayıcı** (Collector) | `gonder.py` + `handle_update.py` | Zamanlanmış/anlık her türlü girdiyi (buton, serbest metin, SLM sınıflandırması) ortak hafızaya doğru şekilde yazar |
| **Değerlendirici** (Evaluator) | `common.py: rutin_serisi_hesapla`, `analiz.py: istatistik_cikar` | Ham veriyi örüntüye çevirir (seri, kaçırma sayısı, tamamlama oranı) |
| **Koç** (Coach) | `analiz.py: koc_onerisi_sun` + `handle_update.py`'deki onay işleme | Örüntüye göre öneri sunar, SLM ile kişiselleştirir; **onay olmadan asla** ortak hafızayı değiştirmez |
| **Rapor** (Reporter) | `analiz.py`'deki haftalık özet + `panel/` | Her şeyi insan-okunabilir/görsel hale getirir (Telegram mesajı, panel) |

Her dosyanın başında `[MULTI-AGENT ROL: ...]` etiketiyle hangi agent'ı
temsil ettiği açıkça belirtilmiştir.

## Roadmap Durumu

- Seviye 1 (✅ tamamlandı): mesaj/ton değişimi + en riskli rutin en üste sıralanır
- Seviye 2 (✅ tamamlandı): Koç, bir rutin 5+ gündür üst üste kaçırılırsa haftalık analiz sırasında duraklatma önerir. **Eşik kod-tabanlı (ne zaman devreye gireceği sabit), ama mesajın içeriği ve cevabına verdiği tavsiye SLM tarafından üretiliyor** — kullanıcının evet/hayır cevabına göre kişiselleştirilmiş, bağlama uygun bir tavsiye veriyor. Onay olmadan Rutinler sekmesini asla değiştirmiyor.
- Seviye 3 (ileride, onaylı): zamanlama (cron) değişikliği
- [x] Multi-agent mimarisi (Toplayıcı / Değerlendirici / Koç / Rapor) — yukarıda dokümante edildi
- [ ] Observability paneli — tasarım tamamlandı, gerçek veriye bağlanması bekliyor

## Güvenlik notu

`.env` ve `service_account.json` dosyaları asla repoya commit edilmemeli.
Gerçek sırlar (secrets) GitHub Actions'a taşındığında Actions Secrets
üzerinden yönetilecek.
