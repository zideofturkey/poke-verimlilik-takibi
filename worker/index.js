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
};
