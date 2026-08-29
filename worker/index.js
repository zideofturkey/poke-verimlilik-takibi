/**
 * Telegram webhook -> GitHub Actions köprüsü.
 *
 * Telegram'dan buton basımı (callback_query) geldiği anda,
 * GitHub'a "repository_dispatch" isteği gönderir. Bu, dinle.yml
 * workflow'unu ANINDA (saniyeler içinde) tetikler - 5 dk/1 saatlik
 * cron beklemesi ortadan kalkar.
 *
 * ONEMLI: Telegram'a 200 OK cevabi ANINDA doner, GitHub'a haber verme
 * islemi arka planda (ctx.waitUntil ile) devam eder. Onceden bu islem
 * Telegram'in cevabini BEKLETIYORDU - eger GitHub'in API'si yavas
 * yanit verirse, Telegram zaman asimina ugrayip AYNI butonu tekrar
 * gonderiyordu (tek tiklamanin cift sayilmasi sorununun kok nedeni buydu).
 *
 * IKINCI BIR "cift tiklama" KAYNAGI (23 Temmuz'da bulundu): yukarıdaki
 * düzeltme SUNUCU tarafı bir sorunu çözüyordu (Telegram'ın webhook'u
 * tekrar göndermesi). Ama answerCallbackQuery (butonun telefonda
 * gösterdiği "yükleniyor" animasyonunu durduran çağrı) SADECE Python
 * tarafında, GitHub Actions runner'ı tamamen ayağa kalktıktan SONRA
 * (soğuk başlangıç dahil 15-40sn) çağrılıyordu - bu süre boyunca
 * kullanıcı hiçbir görsel geri bildirim almıyor, "tıklamam algılanmadı"
 * diye DÜŞÜNÜP GERÇEKTEN İKİNCİ KEZ BASIYORDU. Bu, teknik bir tekrar
 * değil, kullanıcının kendi ikinci tıklaması - iki AYRI callback_query.id
 * ve update_id ile doğrulandı. Çözüm: answerCallbackQuery'yi burada,
 * GitHub'a haber vermeden ÖNCE ve ONUNLA PARALEL, milisaniyeler içinde
 * çağırıyoruz - buton artık GitHub Actions'ı hiç beklemeden anında
 * "tıklandı" gösteriyor.
 *
 * Secrets (wrangler ile ayarlanir, kodda yazili DEGIL):
 *   - GITHUB_TOKEN: repository_dispatch tetikleme yetkisi olan GitHub token
 *   - BOT_TOKEN: Telegram bot token'ı (answerCallbackQuery için)
 *
 * ============================================================
 * scheduled() - GitHub'ın KENDİ cron'una YEDEK tetikleyici
 * ============================================================
 * Ağustos 2026'da gerçek bir olay: GitHub Actions'ın scheduled workflow
 * tetiklemesi (gonder.yml) ciddi şekilde kaymaya/gecikmeye başladı -
 * bazı günler sabah (09:00 TR) ve öğle (13:00 TR) çalıştırmaları SAATLER
 * SONRA (bazen +12 saat) tetiklendi, ÜSTELİK gecikmiş çalıştırma GitHub
 * tarafından hangi cron satırına ait olduğu YANLIŞ raporlandı (21:00
 * hedefli slot 'sabah' görevini çalıştırdı). Bu GitHub'ın kendi status
 * sayfasında da o günlerde art arda "Incident with Actions" kayıtlarıyla
 * doğrulandı - koddan düzeltilemeyen bir platform sorunu. Kullanıcının
 * BAŞKA bir sisteminde de AYNI kayma gözlemlendi - GitHub'a özgü, genel
 * bir zamanlayıcı sorunu.
 *
 * Çözüm: GitHub'ın schedule tetiklemesini TAMAMEN kaldırmak yerine
 * (tek noktadan bağımlılığı artırmamak için), Cloudflare Workers'ın
 * KENDİ Cron Triggers'ı (wrangler.toml'daki [triggers] crons - ayrı bir
 * altyapı, GitHub'ın zamanlayıcısından bağımsız) burada YEDEK bir
 * tetikleyici olarak ekleniyor.
 *
 * KRİTİK KISIT (ilk deploy denemesinde keşfedildi): Cloudflare Workers
 * Free Plan, worker başına EN FAZLA 3 Cron Trigger'a izin veriyor. İlk
 * tasarımda buraya gonder.yml'deki 6 cron satırının BİREBİR aynısı
 * (6 ayrı trigger) konmuştu - `wrangler deploy` bu yüzden Cloudflare
 * API'sinden 400 Bad Request aldı ("Some triggers failed to deploy"),
 * limit aşıldığı için istek TAMAMEN reddedildi (kısmi kabul yok). Çözüm:
 * TEK bir saatlik tetikleyici (`0 * * * *`, wrangler.toml'da) tanımlı,
 * hangi görevin (sabah/hatirlat/aksam/hafta_ortasi/pazar) çalışacağına
 * worker'ın KENDİSİ o anki UTC saat/gün/dakikaya bakarak karar veriyor -
 * GitHub'ın schedule string eşleştirme hatasına (yanlış görev seçme
 * riskine) hiç güvenmeden, VE Cloudflare'in 3-trigger limitinin çok
 * altında (1/3) kalarak.
 *
 * Bilinçli tasarım: GitHub'ın kendi cron'u (gonder.yml'deki `schedule:`)
 * KALDIRILMADI, sadece bu YEDEK eklendi - ikisi birden çalışırsa (GitHub
 * kendi cron'unu da tetiklerse) `sabah()`/`hatirlat()`/`aksam()`
 * içindeki mevcut "zaten cevaplanmış mı" kontrolleri fazladan mesaj
 * gitmesini zaten engelliyor (idempotent), bu yüzden çakışma riski yok.
 */
export default {
  async fetch(request, env, ctx) {
    if (request.method !== "POST") {
      return new Response("OK", { status: 200 });
    }

    let update;
    try {
      update = await request.json();
    } catch (e) {
      return new Response("Bad request", { status: 400 });
    }

    if (update.callback_query) {
      ctx.waitUntil(
        fetch(`https://api.telegram.org/bot${env.BOT_TOKEN}/answerCallbackQuery`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ callback_query_id: update.callback_query.id }),
        }).catch((err) => console.log("answerCallbackQuery hatasi:", err.message))
      );
    }

    if (update.callback_query || update.message) {
      const dispatchPromise = fetch(
        "https://api.github.com/repos/zideofturkey/poke-verimlilik-takibi/dispatches",
        {
          method: "POST",
          headers: {
            "Authorization": `Bearer ${env.GITHUB_TOKEN}`,
            "Accept": "application/vnd.github+json",
            "User-Agent": "poke-webhook-worker",
          },
          body: JSON.stringify({
            event_type: "telegram_update",
            client_payload: { update },
          }),
        }
      ).then(async (githubResp) => {
        if (!githubResp.ok) {
          console.log("GitHub dispatch hatasi:", await githubResp.text());
        }
      }).catch((err) => {
        console.log("GitHub dispatch fetch hatasi:", err.message);
      });

      ctx.waitUntil(dispatchPromise);
    }

    return new Response("OK", { status: 200 });
  },

  async scheduled(event, env, ctx) {
    // Cloudflare Free plan worker basina EN FAZLA 3 Cron Trigger'a izin
    // veriyor (bkz. wrangler.toml'daki not) - bu yuzden 6 ayri saat yerine
    // TEK bir saatlik tetikleyici (`0 * * * *`) kullaniliyor, hangi
    // gorevin calisacagina worker'in kendisi o anki UTC saat/gun/dakikaya
    // bakarak karar veriyor. `event.scheduledTime`, Cloudflare'in bu
    // tetiklemeyi HANGI dakika icin planladigini soyluyor (Date.now()
    // degil - calisirken gecen gecikme yuzunden yanlis saate duşulmesin
    // diye scheduledTime kullaniliyor, tipki GitHub'in kendi schedule
    // string'i yerine bunun tercih edilmesi gibi).
    const zaman = new Date(event.scheduledTime);
    const saat = zaman.getUTCHours();
    const dakika = zaman.getUTCMinutes();
    const gun = zaman.getUTCDay(); // 0=Pazar, 3=Çarşamba

    // Sadece saat başında (dakika 0'a yakın) hareket et - saatlik tetikleyici
    // teorik olarak her zaman :00'da ateşlenir ama gecikme payı için
    // birkaç dakikalık tolerans bırakılıyor.
    if (dakika > 5) return;

    let gorev = null;
    if (gun === 3 && saat === 17) {
      gorev = "hafta_ortasi"; // Çarşamba 20:00 TR
    } else if (gun === 0 && saat === 7) {
      gorev = "pazar"; // Pazar 10:00 TR
    } else if (saat === 6) {
      gorev = "sabah"; // 09:00 TR
    } else if (saat === 10 || saat === 14) {
      gorev = "hatirlat"; // 13:00 / 17:00 TR
    } else if (saat === 18) {
      gorev = "aksam"; // 21:00 TR
    }

    if (!gorev) {
      return; // Bu saat bizim hedef saatlerimizden biri değil, sessizce çık.
    }

    ctx.waitUntil(
      fetch(
        "https://api.github.com/repos/zideofturkey/poke-verimlilik-takibi/actions/workflows/gonder.yml/dispatches",
        {
          method: "POST",
          headers: {
            "Authorization": `Bearer ${env.GITHUB_TOKEN}`,
            "Accept": "application/vnd.github+json",
            "User-Agent": "poke-cron-backup-worker",
          },
          body: JSON.stringify({ ref: "main", inputs: { gorev } }),
        }
      ).then(async (resp) => {
        if (!resp.ok) {
          console.log(`Cloudflare yedek tetikleme hatasi (${gorev}):`, await resp.text());
        } else {
          console.log(`Cloudflare yedek tetikleme basarili: ${gorev}`);
        }
      }).catch((err) => console.log("Cloudflare yedek tetikleme fetch hatasi:", err.message))
    );
  },
};
