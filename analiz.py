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
MODEL = "qwen2.5:3b"
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


def prompt_olustur(veriler):
    if not veriler:
        return None

    satirlar = "\n".join(
        f"- {r['Tarih']}: {r['Görev']} -> {r['Durum']}" for r in veriler
    )
    return (
        "Aşağıda bir kişinin son 7 günlük verimlilik takip verisi var. "
        "Bu veriye bakarak 3-4 cümlelik, samimi ve motive edici bir Türkçe "
        "özet yaz. Hangi rutin/görevlerde iyi gittiğini, hangisinde "
        "zorlandığını ve varsa dikkat çeken bir örüntüyü belirt. "
        "Sadece özeti yaz, başka açıklama ekleme.\n\n"
        f"Veri:\n{satirlar}"
    )


def ollama_sorgula(prompt):
    resp = requests.post(
        OLLAMA_URL,
        json={"model": MODEL, "prompt": prompt, "stream": False},
        timeout=120,
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
