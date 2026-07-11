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
import requests
from common import get_sheet, send_message, TR_TZ

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5:7b"
ANALIZ_GUN_SAYISI = 7


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


def ollama_sorgula(prompt):
    resp = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.3},
        },
        timeout=180,
    )
    resp.raise_for_status()
    return resp.json()["response"].strip()


def main():
    veriler = son_hafta_verisi()
    prompt = prompt_olustur(veriler)

    if prompt is None:
        send_message("📊 Bu hafta için henüz yeterli veri yok, analiz yapılamadı.")
        return

    try:
        ozet = ollama_sorgula(prompt)
    except Exception as e:
        print(f"Ollama hatası: {e}")
        send_message(
            "📊 Haftalık analiz şu an oluşturulamadı (teknik bir sorun oldu), "
            "gelecek hafta tekrar denenecek."
        )
        return

    send_message(f"🧠 Haftalık Analiz (SLM):\n\n{ozet}")
    print("Analiz gönderildi.")


if __name__ == "__main__":
    main()
