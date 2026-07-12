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
    get_bekleyen_soru,
    get_gorevler_sheet,
    get_haftalik_sheet,
    get_sheet,
    hafta_baslangic_str,
    RUTINLER,
    TR_TZ,
)


TELAFI_GUN_SAYISI = 1  # Günlük (ad-hoc) görevler için: sadece 1 gün hatırlatılır, sonra düşer


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

    onceki = get_bekleyen_soru()
    if onceki and onceki != "gunluk_gorev":
        send_message(
            f"⚠️ Not: bir önceki sorumu (\"{onceki}\" ile ilgili) cevaplamadığın "
            "için artık geçersiz sayıyorum, en son bunu soruyorum:"
        )

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


def dun_kacirildi_mi(rutin_isim):
    ws = get_sheet()
    rows = ws.get_all_records()
    dun = dun_str()
    for r in rows:
        if r.get("Görev") == rutin_isim and r.get("Tarih") == dun and r.get("Durum") == "Yapılmadı":
            return True
    return False


def aksam():
    # 1) Sabit rutinler - her gün otomatik sorulur, kullanıcı yazmaz
    send_message("🌙 Akşam kontrolü — günlük rutinlerin:")
    for rutin in RUTINLER:
        butonlar = [
            {"text": "✅ Yaptım", "callback_data": f"rutin_{rutin['id']}_evet"},
            {"text": "❌ Yapmadım", "callback_data": f"rutin_{rutin['id']}_hayir"},
        ]
        satirlar = [butonlar]
        if dun_kacirildi_mi(rutin["isim"]):
            satirlar.append(
                [{"text": "🔁 Dünkü eksiği bugün telafi ettim", "callback_data": f"rutin_{rutin['id']}_telafi"}]
            )
        send_message(f"• {rutin['soru']}", buttons=satirlar)

    # 2) Ad-hoc (sabah tanımlanan) günlük görevler
    ws = get_gorevler_sheet()
    rows = ws.get_all_records()
    bugunku = [
        (i + 2, r)  # +2: başlık satırı + 1-index
        for i, r in enumerate(rows)
        if r["Tarih"] == bugun_str() and r["Durum"] == "Bekliyor"
    ]

    if not bugunku:
        _bosa_vakit_sor()
        return

    send_message("📋 Bugün için yazdığın görevler:")
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

    _bosa_vakit_sor()


def _bosa_vakit_sor():
    if get_bekleyen_soru():
        print("Zaten bekleyen bir soru var, boşa vakit sorusu şimdilik atlanıyor.")
        return
    send_message(
        "Son bir soru: bugün ne kadar boşa vakit geçirdin (YouTube, sosyal "
        "medya vb.)? Kendi cümlelerinle yazabilirsin, ör. \"yaklaşık 40 "
        "dakika Instagram\" gibi."
    )
    set_bekleyen_soru("bosa_vakit")


def pazar():
    onceki = get_bekleyen_soru()
    if onceki and onceki != "haftalik_hedef":
        send_message(
            f"⚠️ Not: bir önceki sorumu (\"{onceki}\" ile ilgili) cevaplamadığın "
            "için artık geçersiz sayıyorum, en son bunu soruyorum:"
        )

    sablon = "\n".join(f"{i}. " for i in range(1, 4))
    mesaj = (
        "🗓️ Yeni hafta başlıyor. Bu haftaki hedeflerin neler?\n\n"
        "Her satıra bir hedef yaz:\n\n"
        f"{sablon}"
    )
    send_message(mesaj)
    set_bekleyen_soru("haftalik_hedef")


def hafta_ortasi():
    ws = get_haftalik_sheet()
    rows = ws.get_all_records()
    hafta = hafta_baslangic_str()
    bu_haftaki = [
        (i + 2, r)
        for i, r in enumerate(rows)
        if r["HaftaBaslangic"] == hafta and r["Durum"] == "Bekliyor"
    ]

    if not bu_haftaki:
        send_message(
            "Bu hafta için tanımlı bir hedef bulamadım — Pazar mesajına cevap "
            "vermeyi unuttun mu? 🤔"
        )
        return

    send_message("📊 Hafta ortası kontrol — hedeflerinin durumu:")
    for row_num, r in bu_haftaki:
        send_message(
            f"• {r['HedefMetni']}",
            buttons=[
                [
                    {"text": "✅ Yolunda", "callback_data": f"hedef_{row_num}_evet"},
                    {"text": "❌ Geride", "callback_data": f"hedef_{row_num}_hayir"},
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
