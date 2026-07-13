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
    get_aktif_rutinler,
    rutin_serisi_hesapla,
    get_deger,
    set_deger,
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
    set_deger("son_sabah_tarihi", bugun_str())

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


def _bugun_cevaplanan_rutinler():
    ws = get_sheet()
    rows = ws.get_all_records()
    bugun = bugun_str()
    return {r["Görev"] for r in rows if r.get("Tarih") == bugun}


def rutin_sorulari_gonder(baslik="🔔 Hatırlatma — henüz cevaplamadığın rutinler:"):
    """Sadece BUGÜN için henüz cevaplanmamış rutinleri sorar. Zaten
    cevaplanmışsa (buton basılmış ya da serbest metinle bildirilmişse)
    bir daha sorulmaz - sessiz kalır. Hem akşam kontrolünde hem günün
    farklı saatlerindeki periyodik hatırlatmalarda kullanılır."""
    rutinler = get_aktif_rutinler()
    cevaplanan = _bugun_cevaplanan_rutinler()
    cevaplanmamislar = [r for r in rutinler if r["isim"] not in cevaplanan]

    if not cevaplanmamislar:
        print("Tüm rutinler bugün için zaten cevaplanmış, hatırlatma gönderilmiyor.")
        return

    rutinler_ile_seri = [
        (rutin, rutin_serisi_hesapla(rutin["isim"])) for rutin in cevaplanmamislar
    ]
    rutinler_ile_seri.sort(key=lambda x: x[1][1], reverse=True)

    satir_metinleri = []
    buton_satirlari = []
    for i, (rutin, (streak, miss_streak)) in enumerate(rutinler_ile_seri, start=1):
        if streak >= 5:
            on_ek = f"🔥 {streak} gündür kesintisiz! "
        elif miss_streak >= 3:
            on_ek = f"⚠️ {miss_streak} gündür kaçırıyorsun. "
        else:
            on_ek = ""
        satir_metinleri.append(f"{i}. {on_ek}{rutin['soru']}")

        butonlar = [
            {"text": f"{i}️⃣ ✅", "callback_data": f"rutin_{rutin['id']}_evet"},
            {"text": f"{i}️⃣ ❌", "callback_data": f"rutin_{rutin['id']}_hayir"},
        ]
        if dun_kacirildi_mi(rutin["isim"]):
            butonlar.append(
                {"text": f"{i}️⃣ 🔁", "callback_data": f"rutin_{rutin['id']}_telafi"}
            )
        buton_satirlari.append(butonlar)

    mesaj = f"{baslik}\n\n" + "\n".join(satir_metinleri)
    send_message(mesaj, buttons=buton_satirlari)


def _sabah_kacti_mi_kontrol_et():
    """Bekçi: GitHub Actions'ın zamanlanmış tetiklemeyi atlamış (drop
    etmiş) olma ihtimaline karşı, sabah mesajının bugün gerçekten
    gidip gitmediğini kontrol eder. Gitmediyse kendisi tetikler."""
    if get_deger("son_sabah_tarihi") != bugun_str():
        print("Sabah mesajı bugün için hiç gitmemiş, bekçi devreye giriyor.")
        send_message("🔧 Fark ettim ki bugünkü sabah mesajım gitmemiş (muhtemelen bir aksaklık oldu), şimdi gönderiyorum:")
        sabah()


def hatirlat():
    """Gün içinde birkaç kez (öğle/akşam üstü) tetiklenir. Sadece o ana
    kadar cevaplanmamış rutinleri sorar."""
    _sabah_kacti_mi_kontrol_et()
    rutin_sorulari_gonder(baslik="🔔 Hatırlatma — henüz cevaplamadığın rutinler:")


def aksam():
    _sabah_kacti_mi_kontrol_et()

    # 1) Rutinler - sadece bugün henüz cevaplanmamış olanlar sorulur
    rutin_sorulari_gonder(baslik="🌙 Akşam kontrolü — günlük rutinlerin:")

    # 2) Ad-hoc (sabah tanımlanan) günlük görevler - hepsi TEK mesajda
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

    satir_metinleri = [f"{i+1}. {r['GorevMetni']}" for i, (_, r) in enumerate(bugunku)]
    buton_satirlari = [
        [
            {"text": f"{i+1}️⃣ ✅", "callback_data": f"gorev_{row_num}_evet"},
            {"text": f"{i+1}️⃣ ❌", "callback_data": f"gorev_{row_num}_hayir"},
        ]
        for i, (row_num, r) in enumerate(bugunku)
    ]
    mesaj = "📋 Bugün için yazdığın görevler:\n\n" + "\n".join(satir_metinleri)
    send_message(mesaj, buttons=buton_satirlari)

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
    "hatirlat": hatirlat,
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in GOREVLER:
        print(f"Kullanım: python gonder.py [{'|'.join(GOREVLER.keys())}]")
        sys.exit(1)

    GOREVLER[sys.argv[1]]()
    print(f"Gönderildi: {sys.argv[1]}")


if __name__ == "__main__":
    main()
