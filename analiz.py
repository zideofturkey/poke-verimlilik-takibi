"""
Haftalık SLM analizi. Takip sekmesindeki son 7 günün verisini toplar,
GitHub Actions runner'ında geçici olarak çalışan yerel bir Ollama modeline
gönderir, çıkan doğal-dil özeti Telegram'a yollar.

Not: Bu model GERÇEK anlamda "on-premise" değildir - GitHub Actions'ın
geçici bulut runner'ında, her çalıştırmada ayağa kaldırılıp kapatılır.
Bu tercih bilinçli yapıldı: gerçek bir yerel/7-24 açık cihaz gerektirmeden
(ki bu "laptop hep açık kalsın" sorununu geri getirirdi) sürdürülebilir,
otomatik bir sistem kurmak için. Detaylar için Sistem Dokümantasyonu'na bakınız.
"""

import datetime
from common import get_sheet, send_message, slm_sorgula, get_aktif_rutinler, rutin_serisi_hesapla, turkce_disi_karakter_var_mi, SLM_MODEL_KALITELI, TR_TZ

ANALIZ_GUN_SAYISI = 7
KOC_DURAKLAMA_ESIGI = 5  # kaç gün üst üste kaçırılırsa duraklatma önerilsin


def son_hafta_verisi():
    ws = get_sheet()
    rows = ws.get_all_records()
    bugun = datetime.datetime.now(TR_TZ).date()
    sinir = bugun - datetime.timedelta(days=ANALIZ_GUN_SAYISI)

    son_veriler = []
    for r in rows:
        try:
            tarih = datetime.datetime.strptime(r["Tarih"], "%Y-%m-%d").date()
        except (ValueError, KeyError):
            continue
        if tarih >= sinir:
            son_veriler.append(r)
    return son_veriler


def istatistik_cikar(veriler):
    """Görev bazında yapıldı/yapılmadı sayılarını Python'da hesaplar -
    modelin kendi başına sayım yapıp hata yapmasını (ve çelişkili
    cümleler kurmasını) önlemek için."""
    sayaclar = {}
    for r in veriler:
        gorev = r["Görev"]
        durum = r["Durum"]
        if gorev not in sayaclar:
            sayaclar[gorev] = {"Yapıldı": 0, "Yapılmadı": 0}
        if durum in sayaclar[gorev]:
            sayaclar[gorev][durum] += 1
    return sayaclar


def prompt_olustur(veriler):
    if not veriler:
        return None

    sayaclar = istatistik_cikar(veriler)
    satirlar = "\n".join(
        f"- {gorev}: {s['Yapıldı']} kez yapıldı, {s['Yapılmadı']} kez yapılmadı"
        for gorev, s in sayaclar.items()
    )
    return (
        "Aşağıda bir kişinin son 7 günlük verimlilik istatistiği var. "
        "SADECE verilen sayılara dayanarak, 3-4 cümlelik akıcı ve tutarlı "
        "bir Türkçe özet yaz. Birbirini çelişen ifadeler kullanma. "
        "En yüksek 'yapıldı' oranına sahip görev(ler)i öv, en yüksek "
        "'yapılmadı' oranına sahip görev(ler)i nazikçe hatırlat. "
        "Sadece özeti yaz, başka açıklama, başlık ya da giriş cümlesi ekleme.\n\n"
        f"İstatistik:\n{satirlar}"
    )


def koc_onerisi_sun():
    """Sürekli kaçırılan rutinler için duraklatma önerisi sunar.
    Mesajın içeriğini SLM üretir (kural: EŞİK sabit/kod tabanlı, İÇERİK
    AI tabanlı). HİÇBİR ZAMAN kendi kendine değiştirmez - her zaman onay ister."""
    for rutin in get_aktif_rutinler():
        _, miss_streak = rutin_serisi_hesapla(rutin["isim"])
        if miss_streak >= KOC_DURAKLAMA_ESIGI:
            prompt = (
                "Sen bir verimlilik koçu botusun (adın Poke). Kullanıcı "
                f"'{rutin['isim']}' rutinini {miss_streak} gündür üst üste "
                "kaçırıyor. Ona bunu nazikçe, yargılamadan belirt ve bir "
                "süreliğine bu rutini duraklatmayı önererek onay iste. "
                "Kısa (2-3 cümle), samimi, destekleyici bir Türkçe mesaj "
                "yaz. SADECE mesajı yaz, başka açıklama ekleme."
            )
            try:
                mesaj = slm_sorgula(prompt, model=SLM_MODEL_KALITELI)
                if turkce_disi_karakter_var_mi(mesaj):
                    raise ValueError("dil kayması tespit edildi")
            except Exception as e:
                print(f"SLM hatası (koç önerisi): {e}")
                mesaj = (
                    f"🧑‍🏫 '{rutin['isim']}' rutinini {miss_streak} gündür "
                    "kaçırıyorsun. Bir süreliğine duraklatalım mı?"
                )

            send_message(
                mesaj,
                buttons=[
                    [
                        {"text": "✅ Evet, duraklat", "callback_data": f"koc_duraklat_{rutin['id']}_evet"},
                        {"text": "❌ Hayır, devam", "callback_data": f"koc_duraklat_{rutin['id']}_hayir"},
                    ]
                ],
            )


def main():
    veriler = son_hafta_verisi()
    prompt = prompt_olustur(veriler)

    if prompt is None:
        send_message("📊 Bu hafta için henüz yeterli veri yok, analiz yapılamadı.")
        return

    try:
        ozet = slm_sorgula(prompt, model=SLM_MODEL_KALITELI)
        if turkce_disi_karakter_var_mi(ozet):
            raise ValueError("dil kayması tespit edildi")
    except Exception as e:
        print(f"SLM hatası: {e}")
        send_message(
            "📊 Haftalık analiz şu an oluşturulamadı (teknik bir sorun oldu), "
            "gelecek hafta tekrar denenecek."
        )
        return

    send_message(f"🧠 Haftalık Analiz (SLM):\n\n{ozet}")
    print("Analiz gönderildi.")

    koc_onerisi_sun()


if __name__ == "__main__":
    main()
