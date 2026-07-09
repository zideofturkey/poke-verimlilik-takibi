"""
GitHub Actions tarafından zamanlanmış olarak çalıştırılır.

Kullanım:
    python gonder.py sabah          -> günlük görevleri sorar (serbest metin)
    python gonder.py aksam          -> bugünkü görevleri kutucuklu sorar
    python gonder.py pazar          -> haftalık hedefleri sorar (serbest metin)
    python gonder.py hafta_ortasi   -> hafta ortası kontrol
"""

import sys
import datetime
from common import (
    send_message,
    set_bekleyen_soru,
    get_gorevler_sheet,
    TR_TZ,
)


TELAFI_GUN_SAYISI = 3  # Kaç güne kadar geriye bakıp "kaçırdın" hatırlatması yapılsın


def bugun_str():
    return datetime.datetime.now(TR_TZ).strftime("%Y-%m-%d")


def dun_str():
    return (datetime.datetime.now(TR_TZ) - datetime.timedelta(days=1)).strftime(
        "%Y-%m-%d"
    )


def gun_etiketi(fark):
    if fark == 1:
        return "dün"
    return f"{fark} gün önce"


def sabah():
    # Son birkaç günün kaçırılan görevlerine bak (telafi mantığı)
    ws = get_gorevler_sheet()
    rows = ws.get_all_records()
    bugun = datetime.datetime.now(TR_TZ).date()

    kacirilanlar = []  # (gun_farki, gorev_metni)
    for r in rows:
        if r["Durum"] != "Yapılmadı":
            continue
        try:
            tarih = datetime.datetime.strptime(r["Tarih"], "%Y-%m-%d").date()
        except (ValueError, KeyError):
            continue
        fark = (bugun - tarih).days
        if 1 <= fark <= TELAFI_GUN_SAYISI:
            kacirilanlar.append((fark, r["GorevMetni"]))

    sablon = "\n".join(f"{i}. " for i in range(1, 6))
    mesaj = (
        "🌅 Günaydın! Bugün ne yapacaksın?\n\n"
        "Her satıra bir görev yaz (satır silebilir ya da gerekirse "
        "yeni numarayla ekleyebilirsin):\n\n"
        f"{sablon}"
    )
    send_message(mesaj)
    set_bekleyen_soru("gunluk_gorev")

    if kacirilanlar:
        kacirilanlar.sort(key=lambda x: x[0])
        satirlar = "\n".join(
            f"• {gorev} ({gun_etiketi(fark)})" for fark, gorev in kacirilanlar
        )
        send_message(
            f"📌 Kaçırdıkların:\n{satirlar}\n\n"
            "Bugün bunlardan birini de eklemek istersen, yukarıdaki listeye "
            "bir satır olarak yazman yeterli."
        )


def aksam():
    ws = get_gorevler_sheet()
    rows = ws.get_all_records()
    bugunku = [
        (i + 2, r)  # +2: başlık satırı + 1-index
        for i, r in enumerate(rows)
        if r["Tarih"] == bugun_str() and r["Durum"] == "Bekliyor"
    ]

    if not bugunku:
        send_message(
            "Bugün için tanımlı bir görev bulamadım — sabah mesajına cevap "
            "vermeyi unuttun mu? 🤔"
        )
        return

    send_message("🌙 Akşam kontrolü — bugünkü görevlerin durumu:")
    for row_num, r in bugunku:
        send_message(
            f"• {r['GorevMetni']}",
            buttons=[
                [
                    {"text": "✅ Yaptım", "callback_data": f"gorev_{row_num}_evet"},
                    {"text": "❌ Yapmadım", "callback_data": f"gorev_{row_num}_hayir"},
                ]
            ],
        )


def pazar():
    send_message("🗓️ Yeni hafta başlıyor. Bu haftaki hedeflerin neler?")
    set_bekleyen_soru("haftalik_hedef")


def hafta_ortasi():
    send_message(
        "📊 Hafta ortası kontrol: bu hafta hedeflerinin neresindesin?",
        buttons=[
            [
                {"text": "İyi gidiyorum", "callback_data": "hafta_iyi"},
                {"text": "Geride kaldım", "callback_data": "hafta_geride"},
            ]
        ],
    )


GOREVLER = {
    "sabah": sabah,
    "aksam": aksam,
    "pazar": pazar,
    "hafta_ortasi": hafta_ortasi,
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in GOREVLER:
        print(f"Kullanım: python gonder.py [{'|'.join(GOREVLER.keys())}]")
        sys.exit(1)

    GOREVLER[sys.argv[1]]()
    print(f"Gönderildi: {sys.argv[1]}")


if __name__ == "__main__":
    main()
