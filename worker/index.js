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
 * Secrets (wrangler ile ayarlanir, kodda yazili DEGIL):
 *   - GITHUB_TOKEN: repository_dispatch tetikleme yetkisi olan GitHub token
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
