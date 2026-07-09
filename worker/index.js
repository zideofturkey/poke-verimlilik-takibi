/**
 * Telegram webhook -> GitHub Actions köprüsü.
 *
 * Telegram'dan buton basımı (callback_query) geldiği anda,
 * GitHub'a "repository_dispatch" isteği gönderir. Bu, dinle.yml
 * workflow'unu ANINDA (saniyeler içinde) tetikler - 5 dk/1 saatlik
 * cron beklemesi ortadan kalkar.
 *
 * Secrets (wrangler ile ayarlanır, kodda yazılı DEĞİL):
 *   - GITHUB_TOKEN: repository_dispatch tetikleme yetkisi olan GitHub token
 */

export default {
  async fetch(request, env) {
    if (request.method !== "POST") {
      return new Response("OK", { status: 200 });
    }

    let update;
    try {
      update = await request.json();
    } catch (e) {
      return new Response("Bad request", { status: 400 });
    }

    // Sadece buton basımlarını (callback_query) ilgilendiriyoruz
    if (update.callback_query) {
      const githubResp = await fetch(
        "https://api.github.com/repos/zideofturkey/poke-verimlilik-takibi/dispatches",
        {
          method: "POST",
          headers: {
            "Authorization": `Bearer ${env.GITHUB_TOKEN}`,
            "Accept": "application/vnd.github+json",
            "User-Agent": "poke-webhook-worker",
          },
          body: JSON.stringify({
            event_type: "telegram_callback",
            client_payload: { update },
          }),
        }
      );

      if (!githubResp.ok) {
        console.log("GitHub dispatch hatası:", await githubResp.text());
      }
    }

    // Telegram'a hemen 200 dönmek önemli, yoksa tekrar tekrar dener
    return new Response("OK", { status: 200 });
  },
};
