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

4. Ana script'ler (elle test için, normalde GitHub Actions tetikler):
   ```
   python gonder.py sabah|hatirlat|aksam|hafta_ortasi|pazar
   python handle_update.py    # webhook tarafından CLIENT_PAYLOAD ile tetiklenir
   python dinle.py            # saatlik yedek poller
   python analiz.py           # haftalık SLM analizi + Koç önerileri
   python temizle.py          # eski veri temizliği
   python panel_veri_uret.py  # panel/data.json üretir
   ```

**Rutinler vs. Günlük Görevler (önemli ayrım):**
- **Rutinler** (Sheets'teki `Rutinler` sekmesi — kullanıcı doğrudan görüp düzenleyebilir) her akşam/gün içi hatırlatmada **otomatik** sorulur, kullanıcı yazmaz. Kaçırılırsa, ertesi gün "🔁 Dünkü eksiği telafi ettim" butonu görünür.
- **Günlük görevler** kullanıcının sabah yazdığı (ya da istediği an serbest metinle eklediği) tek seferlik işlerdir. Kaçırılırsa sadece **1 gün** hatırlatılır, sonra düşer — sürekli nag etmez.

## SLM Entegrasyonu — Mimari Kararı

Sistem **iki ayrı yerel model** kullanır, ikisi de Ollama üzerinden,
GitHub Actions'ın geçici bulut runner'ı içinde çalışır:
- **qwen2.5:3b** — günlük sınıflandırma ve serbest-metin cevapları (hız/güvenilirlik öncelikli, her mesajda çalışır)
- **qwen2.5:7b** — haftalık analiz ve Koç önerileri (kalite öncelikli, haftada birkaç kez çalışır)

**Bu, katı anlamda "on-premise" değildir** — bilinçli bir tercih:
gerçek bir 7/24 açık yerel cihaz (laptop veya Raspberry Pi) gerektirmek,
projenin başında çözdüğümüz "laptop'tan bağımsızlık" kazanımını geri
alırdı. Sürdürülebilirlik ve otomasyon, katı on-premise tanımına sadık
kalmaktan önceliklendirildi. Model yine de açık kaynak ve küçük (SLM)
kategorisinde — sadece barındığı altyapı bulut, hesaplama bulutta
üçüncü parti bir API'ye değil, bizim kontrolümüzdeki bir runner'da
gerçekleşiyor. **VPS'e geçiş planlanıyor** — bu, hem gerçek on-premise
tanımını karşılayacak hem de günlük model daha büyük/kaliteli bir
modele yükseltilebilecek (şu an 3B'nin sınıflandırma hataları buna
bağlı - bkz. Roadmap).

## Mimari (güncel)

- `common.py` — paylaşılan Telegram/Sheets yardımcı fonksiyonları + genel görev/durum yönetimi
- `gonder.py` — proaktif mesajlar: `sabah`, `hatirlat` (günde 3 kez, sadece cevapsız rutinler), `aksam`, `pazar`, `hafta_ortasi`
- `handle_update.py` — buton basımlarını VE serbest metin cevaplarını işler (webhook tarafından anlık tetiklenir)
- `dinle.py` — webhook başarısız olursa diye saatte bir çalışan yedek (aynı işleme mantığını kullanır)
- `analiz.py` — haftalık SLM analizi (Değerlendirici + Koç + Rapor rolleri)
- `temizle.py` — eski veri temizliği (haftalık)
- `panel_veri_uret.py` — panel/data.json'ı gerçek Sheets/GitHub verisinden üretir
- `panel/` — gözlemlenebilirlik paneli (statik HTML, Cloudflare Workers üzerinde barındırılıyor)
- `worker/` — Cloudflare Worker, Telegram webhook'unu GitHub Actions'a anlık iletir
- `.github/workflows/` — `gonder.yml` (zamanlama), `webhook.yml` (anlık işleme), `dinle.yml` (yedek), `analiz.yml` (haftalık), `temizle.yml` (haftalık), `panel_guncelle.yml` (panel verisini üretir, commit'ler VE otomatik olarak Cloudflare'e `wrangler deploy` ile yayınlar — 30dk hedefli ama GitHub'ın zamanlamasına bağlı)

**Google Sheets sekmeleri:**
- `Takip` — tüm tamamlanan/kaçırılan görevlerin log'u
- `GunlukGorevler` — her günün serbest-metinle tanımlanan görev listesi + durumu
- `HaftalikHedefler` — haftalık hedef metinleri
- `Rutinler` — kullanıcının doğrudan düzenleyebildiği rutin listesi (isim, soru, aktif/pasif)
- `Durum` — hangi serbest-metin sorusunun cevabı bekleniyor (basit key-value)
- `SLMLog` — sınıflandırma kararlarının tam prompt/cevap kaydı (panelin Teknik sekmesi için)
- `HataLog` — hataların kalıcı özet kaydı (panelin Teknik sekmesi için)
- `HaftalikRutinler` — haftalık (tekrarlayan, günü önemsiz) rutin tanımları
- `HaftalikRutinTakip` — her haftanın otomatik oluşan haftalık rutin takip kaydı

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
- [x] SLM güvenilirlik düzeltmesi: günlük sınıflandırma/cevaplar artık daha küçük/hızlı model (qwen2.5:3b) kullanıyor, haftalık analiz + Koç önerileri kalite öncelikli büyük modelde (qwen2.5:7b) kalıyor.
- [x] Gerçek hata teşhis altyapısı: SLM çağrıları hata verirse artık tahmin edilmiyor - tam traceback + Ollama'nın kendi loglarını `son_hata.txt`'ye kaydedip commit'liyor. Bu sayede kök neden bulundu: Ollama'nın kendi programını (binary) önbelleğe almak, `llama-server` alt bileşeni eksik/bozuk bir kurulumu sürekli geri yüklüyordu. Artık SADECE model dosyaları önbelleğe alınıyor, program kurulumu her seferinde taze yapılıyor.
- [x] SLM otomatik yeniden deneme: Ollama'nın alt süreci (llama-server) nadiren çöküyor (ör. segfault) - bu durumda süreç tamamen öldürülüp taze başlatılarak toplam 3 kez denenir (önceden 2), denemeler arası bekleme artırıldı. Ayrıca kurulum sırasında Ollama'nın kendi kendine başlattığı bir servisle bizim başlattığımız servisin çakışması (port zaten kullanımda hatası) engellendi.
- [x] Serbest metinde tarih algılama: "dün" ya da "15 Temmuz" gibi bir tarih referansı geçen boşa-vakit beyanları ve rutin-tamamlama bildirimleri artık o beyan edilen güne kaydediliyor, mesajın gönderildiği güne değil.
- [x] Telafi mantığı düzeltmesi: 🔁 butonuna basıldığında artık BUGÜN "Yapıldı" (tam tamamlanmış), DÜN "Telafi" (nötr) olarak işaretleniyor - önceden sadece bugüne "Telafi" yazılıyordu, dünkü kayıt hiç düzeltilmiyordu.
- [x] Başlık satırı ayıklama düzeltmesi: artık ":" ile bitmeyen serbest başlık cümleleri de (ör. "Günaydın, bugünün görevlerini yazıyorum") doğru ayıklanıyor - mesajda numaralı satır varsa SADECE numaralı satırlar madde sayılır.
- [x] "Boşa geçen vakit" beyanları artık gerçekten kullanılıyor: haftalık analiz özetine dahil ediliyor (önceden toplanıp hiç okunmuyordu), anlık cevap da genel "not aldım" yerine içeriğe gerçekten değinen bir yorum üretiyor.
- [x] dinle.py + webhook çakışma düzeltmesi: aynı Telegram update'inin nadiren hem anlık webhook hem saatlik yedek (dinle.py) tarafından işlenmesi ihtimaline karşı, Sheets üzerinden hızlı bir "zaten işlendi mi" kontrolü eklendi.
- [x] SLM karar logu: sınıflandırma kararlarının tam prompt/cevabı artık `SLMLog` sekmesine kaydediliyor ve panelin Teknik sekmesinde gösteriliyor (sadece bu özelliğin eklendiği tarihten sonrası için).
- [x] Panelin Teknik sekmesi güçlendirildi: gerçek çalıştırma süreleri (GitHub API'den hesaplanıyor), workflow türüne göre başarı oranı + ortalama süre kırılımı, SLM kategori dağılımı (Poke'un gerçekte ne için kullanıldığının görünümü), ve kalıcı bir hata geçmişi (`HataLog` sekmesi — önceden hatalar sadece geçici bir dosyada tutulup kayboluyordu, şimdi zaman içindeki hata sıklığı görülebiliyor).
- [x] Haftalık hedef hatırlatması artık rutinlerle aynı mantıkla periyodik: Pazartesi/Çarşamba/Cuma günleri `hatirlat()` içinde otomatik kontrol ediliyor (hangi gün eklenmiş olurlarsa olsunlar - önceden sadece Çarşamba tek seferlik kontrol vardı, hafta ortasından SONRA girilen hedefler hiç yakalanmıyordu). `pazar()` de artık yeni haftayı sormadan önce, biten haftanın kalan hedeflerini son bir kez soruyor.
- [x] KRİTİK DÜZELTME: `hedef_` (haftalık hedef Yolunda/Geride) butonları için hiç işleme kodu yoktu - tıklamak hiçbir şey yapmıyordu (ne Sheets güncelleniyordu ne cevap geliyordu). Artık işleniyor ve Sheets'e tutarlı şekilde (Yapıldı/Yapılmadı) yazıyor.
- [x] Haftalık hedef hatırlatma mesajları artık (rutinler/görevler gibi) TEK mesajda, çok satırlı butonlarla geliyor - önceden her hedef ayrı mesaj olarak dağınık geliyordu.
- [x] Rutinlere yeni bir `TelafiEdilebilir` sütunu eklendi (Sheets'te doğrudan düzenlenebilir) - bazı rutinler (ör. "sabah telefonsuzluğu" gibi bir şeyi YAPMAMAKLA ilgili olanlar) doğası gereği telafi edilemez, 🔁 butonu artık sadece bunun TRUE olduğu rutinlerde gösteriliyor.
- [x] **Haftalık Rutinler** — günlük rutinlerin haftalık eşleniği eklendi. Yeni sekmeler: `HaftalikRutinler` (tanımlar, Sheets'ten düzenlenebilir - ör. "Oda tozu alma") ve `HaftalikRutinTakip` (her haftanın otomatik oluşan takip kaydı). Hangi gün tamamlandığı önemli değil, hafta içinde herhangi bir zaman. Hatırlatma haftalık hedeflerle aynı günlerde (Pzt/Çar/Cum) geliyor, buton VEYA serbest metinle ("oda tozunu aldım") tamamlanabiliyor.
- [x] **KRİTİK DÜZELTME — mesaj sessizce kaybolma riski:** dinle/webhook çakışma korumasının "işlendi" damgası, önceden işlem BAŞLARKEN basılıyordu - eğer işlem sırasında beklenmedik bir çökme olursa, mesaj hem kullanıcıya hiç cevap vermeden hem de dinle.py'nin bir daha denemeyeceği şekilde kayboluyordu. Artık damga SADECE başarılı tamamlanınca basılıyor. Ayrıca hem webhook hem dinle.py'nin en dışına bir güvenlik ağı eklendi - ne olursa olsun kullanıcı artık asla sessiz kalmıyor, en azından "işleyemedim, tekrar dener misin" cevabı gidiyor.
- [x] **Deterministik ön-sınıflandırma:** "bugünkü/haftalık görevlerimi kaydet" + numaralı liste gibi çok net kalıplar, artık SLM'e HİÇ SORULMADAN kod ile (hatasız) sınıflandırılıyor. Küçük model bu kalıpta tekrar tekrar hata yapıp (SOHBET sanıp "kaydettim" diye hayali bir cevap üretiyordu - halüsinasyon) veri kaybına sebep oluyordu. SLM artık sadece gerçekten belirsiz durumlar (sorgu, sohbet, tek görev ekleme, rutin tamamlama, boşa vakit) için kullanılıyor.
- [x] SOHBET/SORGULA kategorilerinin cevabına, hiçbir zaman yapılmamış bir eylemi ("kaydettim", "ekledim") yapmış gibi iddia etmemesi için açık bir kural eklendi (halüsinasyon riskini azaltmak için).
- [x] YENI_GOREV yolu artık önce numaralı-satır yapısını (satirlari_ayikla) kontrol ediyor - önceden sadece GUNLUK_GOREV/HAFTALIK_HEDEF yolları başlık cümlelerini doğru ayıklıyordu, YENI_GOREV kendi ayrı (daha az güvenilir) mantığını kullanıyordu.
- [x] Rutin butonlarına tarih gömülmesi: artık her rutin butonu hangi güne ait olduğunu taşıyor - dünün cevaplanmamış bir sorusunu bugün (geç de olsa) işaretlersen, doğru güne (dün) kaydediliyor, bugüne değil. Eski (bu düzeltmeden önce gönderilmiş) butonlar için geriye dönük uyumluluk korunuyor.
- [x] SORGULA sınıflandırması güçlendirildi: "bugünkü rutin tamamlama listemi gönderir misin" gibi soru-kipli cümleler artık yanlışlıkla GUNLUK_GOREV sanılmıyor (test edilip doğrulandı). SORGULA cevaplayıcı da genişletildi: artık "seri/streak" ve "bu hafta nasıl gidiyorum" tarzı sorular da (deterministik, gerçek veriye dayalı) cevaplanabiliyor - önceden sadece "bugün" kapsamı vardı.
- [x] GUNLUK_GOREV/HAFTALIK_HEDEF karışması düzeltildi: "bugünkü görevlerim: ..." gibi mesajlar bazen yanlışlıkla haftalık hedef sanılıp yanlış sekmeye yazılıyordu - "bugün/bugünkü" ve "hafta/haftalık" kelimeleri için açık ayrım kuralı eklendi.
- [x] GunlukGorevler sekmesi bir noktada Google Sheets'in "Tabloya Dönüştür" özelliğiyle bir Tabloya dönüşmüş - bu, gspread'in `append_row` fonksiyonunun bazen sessizce başarısız olmasına sebep oluyordu (canlı sistemde de aynı riski taşıyordu). **Kalıcı düzeltme:** `guvenli_append_row()` adında yeni bir yardımcı fonksiyon eklendi - önce normal `append_row`'u dener, başarısız olursa ham Google Sheets API'siyle (values.append) otomatik tekrar dener. Görev/hedef ekleyen tüm canlı kod yolları (GUNLUK_GOREV, HAFTALIK_HEDEF, YENI_GOREV) artık bunu kullanıyor.
- [x] Üçüncü durum: "Telafi" — dünkü kaçırmayı bugün telafi etmek, ne tam zamanında yapmış (Yapıldı) ne de hiç yapmamış (Yapılmadı) gibi sayılmaz; ayrı, nötr bir kategori. Seri (streak) hesabında nötr durak noktası, panelde ayrı bir rozetle (🔁, amber renk), haftalık analizde ayrı bir istatistik olarak gösteriliyor.
- [x] Çift log düzeltmesi: aynı gün + aynı görev için ikinci bir kayıt gelirse (çift tıklama, önce Evet sonra Hayır) YENİ satır açılmaz, var olan satır güncellenir
- [x] Bayat "bekleyen soru" düzeltmesi: bir soru cevaplanmadan günler geçerse, otomatik olarak geçersiz sayılıp temizlenir - sonsuza kadar sonraki soruları (ör. boşa vakit) engellemez
- [x] Çift tıklama kök neden düzeltmesi: Cloudflare Worker artık Telegram'a ANINDA 200 dönüyor, GitHub'a haber verme işlemi arka planda (ctx.waitUntil) devam ediyor. Önceden Telegram'ın cevabı GitHub'ın yanıt vermesini bekliyordu, yavaş bir yanıt Telegram'ın aynı butonu tekrar göndermesine (çift sayılmasına) sebep oluyordu.
- [x] Tarih tutarlılığı düzeltmesi: gece yarısından sonra bir önceki günün ad-hoc görevini işaretlersen, artık Takip'e görevin KENDİ tarihiyle (etkileşim anının tarihiyle değil) loglanıyor - GunlukGorevler ile Takip arasında tarih uyuşmazlığı olmaz
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
- [x] Observability paneli — Kişisel sekme tamamen gerçek veriye bağlı; Teknik sekme workflow geçmişi + Koç kararları gerçek, SLM karar logu sadece bu özelliğin eklendiği tarihten sonrası için mevcut. `https://poke-observability.ediz-kacmaz19.workers.dev` adresinde canlı.

## Güvenlik notu

`.env` ve `service_account.json` dosyaları asla repoya commit edilmemeli.
Gerçek sırlar (secrets) GitHub Actions'a taşındığında Actions Secrets
üzerinden yönetilecek.
