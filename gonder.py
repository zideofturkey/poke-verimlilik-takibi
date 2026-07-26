"""
[MULTI-AGENT ROL: TOPLAYICI (Collector) — soru sorma tarafı]
Bu dosya, Toplayıcı agent'ının "veri isteme" yarısıdır: zamanlanmış
tetiklemelerle kullanıcıya soru sorar (rutin, günlük görev, haftalık hedef).
Cevapları işleyip ortak hafızaya (Sheets) yazan diğer yarı handle_update.py'de.
Diğer agent'larla (Değerlendirici/Koç/Rapor) DOĞRUDAN konuşmaz - hepsi
ortak Sheets üzerinden dolaylı haberleşir (blackboard mimarisi).

GitHub Actions tarafından zamanlanmış olarak çalıştırılır.

Kullanım:
    python gonder.py sabah          -> günlük görevleri sorar (serbest metin)
    python gonder.py aksam          -> bugünkü görevleri kutucuklu sorar
    python gonder.py pazar          -> haftalık hedefleri sorar (serbest metin)
    python gonder.py hafta_ortasi   -> hafta ortası kontrol
"""

import sys
import random
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
    get_aktif_haftalik_rutinler,
    get_haftalik_rutin_takip_sheet,
    rutin_serisi_hesapla,
    cevaplanan_rutinler,
    dun_kacirildi_mi,
    aforizma_sec,
    aforizma_gonderildi_isaretle,
    get_deger,
    set_deger,
    KULLANICI_ADI,
    TR_TZ,
)


TELAFI_GUN_SAYISI = 1  # Günlük (ad-hoc) görevler için: sadece 1 gün hatırlatılır, sonra düşer
SURESI_DOLMA_GUN_SAYISI = 3  # Günlük görevler: bu kadar gündür 'Bekliyor' kalırsa 'Süresi Doldu'
HAFTALIK_SURESI_DOLMA_GUN_SAYISI = 14  # Haftalık hedefler: kendi haftası + 1 hafta pay (2 hafta) sonra


def bugun_str():
    return datetime.datetime.now(TR_TZ).strftime("%Y-%m-%d")


def _suresi_dolanlari_isaretle_ve_bildir():
    """3+ gündür 'Bekliyor' kalan günlük görevleri ve kendi haftası + 1
    hafta paydan (14 gün) sonra hâlâ 'Bekliyor' kalan haftalık hedefleri
    'Süresi Doldu' olarak işaretler. BİLİNÇLİ OLARAK 'Yapılmadı' DEĞİL -
    kullanıcının gerçekten yapmadığını değil, sadece hiç cevap vermediğini
    biliyoruz; bunu kesin bir başarısızlık gibi kaydetmek yanlış negatif
    üretip seri/panel istatistiklerini bozabilirdi. Rutinler bilinçli
    olarak KAPSAM DIŞI - kullanıcı dünden öncesini zaten hatırlayamıyor,
    ve 'dün kaçırdın mı' sorgusu (telafi mekanizması) zaten sistemde var.
    Her sabah() çağrısında çalışır (günde bir kez, saat 09:00 TR)."""
    bugun = datetime.datetime.now(TR_TZ).date()
    bildirimler = []

    ws_gorev = get_gorevler_sheet()
    for i, r in enumerate(ws_gorev.get_all_records()):
        if r.get("Durum") != "Bekliyor":
            continue
        try:
            tarih = datetime.datetime.strptime(r["Tarih"], "%Y-%m-%d").date()
        except (ValueError, KeyError):
            continue
        if (bugun - tarih).days >= SURESI_DOLMA_GUN_SAYISI:
            ws_gorev.update_cell(i + 2, 4, "Süresi Doldu")
            bildirimler.append(f"📋 {r['GorevMetni']} ({r['Tarih']})")

    ws_hedef = get_haftalik_sheet()
    for i, r in enumerate(ws_hedef.get_all_records()):
        if r.get("Durum") != "Bekliyor":
            continue
        try:
            hafta_tarih = datetime.datetime.strptime(r["HaftaBaslangic"], "%Y-%m-%d").date()
        except (ValueError, KeyError):
            continue
        if (bugun - hafta_tarih).days >= HAFTALIK_SURESI_DOLMA_GUN_SAYISI:
            ws_hedef.update_cell(i + 2, 3, "Süresi Doldu")
            bildirimler.append(f"🎯 {r['HedefMetni']} ({r['HaftaBaslangic']} haftası)")

    if bildirimler:
        liste = "\n".join(bildirimler)
        send_message(
            "⏳ Uzun süredir cevapsız kalan şunları 'Süresi Doldu' olarak "
            f"işaretledim (gerçekten yaptıysan söyle, düzeltirim):\n{liste}"
        )


def dun_str():
    return (datetime.datetime.now(TR_TZ) - datetime.timedelta(days=1)).strftime(
        "%Y-%m-%d"
    )


def gun_etiketi(fark):
    if fark == 1:
        return "dün"
    return f"{fark} gün önce"


def sabah():
    _suresi_dolanlari_isaretle_ve_bildir()

    # Son birkaç günün kaçırılan görevlerine bak (telafi mantığı)
    ws = get_gorevler_sheet()
    rows = ws.get_all_records()
    bugun = datetime.datetime.now(TR_TZ).date()

    # Bugün için zaten görev girilmiş mi? (ör. kullanıcı soru sorulmadan
    # kendiliğinden yazmış olabilir) - öyleyse aynı soruyu tekrar sorma
    bugun_zaten_var = any(r["Tarih"] == bugun_str() for r in rows)
    if bugun_zaten_var:
        print("Bugün için zaten görev listesi var, sabah mesajı atlanıyor.")
        set_deger("son_sabah_tarihi", bugun_str())
        return

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
        f"🌅 Günaydın {KULLANICI_ADI}! Bugün ne yapacaksın?\n\n"
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


def rutin_sorulari_gonder(baslik="🔔 Hatırlatma — henüz cevaplamadığın rutinler:"):
    """Sadece BUGÜN için henüz cevaplanmamış rutinleri sorar. Zaten
    cevaplanmışsa (buton basılmış ya da serbest metinle bildirilmişse)
    bir daha sorulmaz - sessiz kalır. Hem akşam kontrolünde hem günün
    farklı saatlerindeki periyodik hatırlatmalarda kullanılır."""
    rutinler = get_aktif_rutinler()
    cevaplanan = cevaplanan_rutinler()
    cevaplanmamislar = [r for r in rutinler if r["isim"] not in cevaplanan]

    if not cevaplanmamislar:
        print("Tüm rutinler bugün için zaten cevaplanmış, hatırlatma gönderilmiyor.")
        return

    rutinler_ile_seri = [
        (rutin, rutin_serisi_hesapla(rutin["isim"])) for rutin in cevaplanmamislar
    ]
    rutinler_ile_seri.sort(key=lambda x: x[1][1], reverse=True)

    bugun = bugun_str()
    butonlar_icin_bugun = bugun  # okunabilirlik için

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
            {"text": f"{i}️⃣ ✅", "callback_data": f"rutin_{rutin['id']}_{butonlar_icin_bugun}_evet"},
            {"text": f"{i}️⃣ ❌", "callback_data": f"rutin_{rutin['id']}_{butonlar_icin_bugun}_hayir"},
        ]
        if rutin.get("telafi_edilebilir", True) and dun_kacirildi_mi(rutin["isim"]):
            butonlar.append(
                {"text": f"{i}️⃣ 🔁", "callback_data": f"rutin_{rutin['id']}_{butonlar_icin_bugun}_telafi"}
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


def haftalik_rutin_sorulari_gonder():
    """Haftalık rutinlerin (ör. 'oda tozu alma') o haftaki durumunu
    kontrol eder. Yeni bir hafta için henüz takip satırı yoksa otomatik
    oluşturur (Bekliyor). Sadece hâlâ 'Bekliyor' olanları sorar, günü
    önemli değil - hafta içinde herhangi bir gün tamamlanabilir."""
    rutinler = get_aktif_haftalik_rutinler()
    if not rutinler:
        return

    ws = get_haftalik_rutin_takip_sheet()
    rows = ws.get_all_values()
    hafta = hafta_baslangic_str()

    mevcut_id_seti = {row[1] for row in rows[1:] if len(row) >= 2 and row[0] == hafta}
    for rutin in rutinler:
        if rutin["id"] not in mevcut_id_seti:
            ws.append_row([hafta, rutin["id"], rutin["isim"], "Bekliyor"])

    # Taze durumu tekrar oku (az önce eklenen satırlar dahil)
    rows = ws.get_all_values()
    bekleyenler = [
        (i + 1, row[2])  # satır no (1-indexed, header dahil), isim
        for i, row in enumerate(rows[1:], start=1)
        if row[0] == hafta and row[3] == "Bekliyor"
    ]

    if not bekleyenler:
        return

    send_message(
        "🗓️ Bu haftaki tekrarlayan işlerin durumu:\n\n" +
        "\n".join(f"{i+1}. {isim}" for i, (_, isim) in enumerate(bekleyenler)),
        buttons=[
            [
                {"text": f"{i+1}️⃣ ✅", "callback_data": f"haftarutin_{satir_no}_evet"},
                {"text": f"{i+1}️⃣ ❌", "callback_data": f"haftarutin_{satir_no}_hayir"},
            ]
            for i, (satir_no, isim) in enumerate(bekleyenler)
        ],
    )


def hatirlat():
    """Gün içinde birkaç kez (öğle/akşam üstü) tetiklenir. Sadece o ana
    kadar cevaplanmamış rutinleri sorar. Haftada 3 kez (Pazartesi/
    Çarşamba/Cuma) hâlâ bekleyen haftalık hedefleri de kontrol eder -
    hangi gün eklenmiş olurlarsa olsunlar (ör. hedefler Perşembe günü
    yazılmışsa bile artık kaçırılmıyor)."""
    _sabah_kacti_mi_kontrol_et()
    rutin_sorulari_gonder(baslik="🔔 Hatırlatma — henüz cevaplamadığın rutinler:")

    bugun_gun_no = datetime.datetime.now(TR_TZ).weekday()  # 0=Pazartesi, 4=Cuma
    if bugun_gun_no in (0, 2, 4):
        haftalik_hedef_sorulari_gonder()
        haftalik_rutin_sorulari_gonder()


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
    """ÖNCEDEN: eğer başka bir soru zaten bekleniyorsa (ör. cevaplanmamış
    haftalık hedef hatırlatması) bu SORU SESSİZCE hiç sorulmuyordu -
    kullanıcı fark etmeden akşam mesajını hiç almayabiliyordu (gerçek bir
    olayda tam olarak bu yaşandı: 21:00'de haftalık hedef hatırlatması
    cevapsız kaldı, 22:02'deki akşam kontrolünde bu yüzden boşa-vakit
    sorusu hiç gitmedi). Bu, kodun geri kalanıyla (sabah()/pazar()) TUTARSIZDI
    - onlar aynı durumda SESSİZCE atlamak yerine önce eski soruyu geçersiz
    saydığını açıkça söylüyor, sonra yeni soruyu soruyorlar. Artık aynı
    tutarlı desen kullanılıyor."""
    onceki = get_bekleyen_soru()
    if onceki and onceki != "bosa_vakit":
        send_message(
            f"⚠️ Not: bir önceki sorumu (\"{onceki}\" ile ilgili) cevaplamadığın "
            "için artık geçersiz sayıyorum, en son bunu soruyorum:"
        )
    send_message(
        "Son bir soru: bugün ne kadar boşa vakit geçirdin (YouTube, sosyal "
        "medya vb.)? Kendi cümlelerinle yazabilirsin, ör. \"yaklaşık 40 "
        "dakika Instagram\" gibi."
    )
    set_bekleyen_soru("bosa_vakit")


def pazar():
    # Önce bitmekte olan haftanın hâlâ bekleyen hedefleri/rutinleri var mı
    # diye son bir kez kontrol et (haftalık Koç analizinden ÖNCE) - hangi
    # gün eklenmiş olurlarsa olsunlar.
    haftalik_hedef_sorulari_gonder()
    haftalik_rutin_sorulari_gonder()

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


def haftalik_hedef_sorulari_gonder(sessiz_gecerse_hicbir_sey_yapma=True):
    """Mevcut haftanın hâlâ 'Bekliyor' durumundaki hedeflerini sorar -
    HANGİ GÜN eklenmiş olursa olsun (ör. hedefler Perşembe günü
    yazılmışsa bile). Zaten cevaplanmışsa (hepsi Yolunda/Geride
    işaretlenmişse) sessiz kalır, spam yapmaz. Hem periyodik hatırlatma
    (hatirlat) hem hafta sonu son kontrolü (pazar) hem de hafta ortası
    (hafta_ortasi) için tek, paylaşılan bir kod yolu."""
    ws = get_haftalik_sheet()
    rows = ws.get_all_records()
    hafta = hafta_baslangic_str()
    bu_haftaki = [
        (i + 2, r)
        for i, r in enumerate(rows)
        if r["HaftaBaslangic"] == hafta and r["Durum"] == "Bekliyor"
    ]

    if not bu_haftaki:
        if not sessiz_gecerse_hicbir_sey_yapma:
            send_message(
                "Bu hafta için tanımlı bir hedef bulamadım — Pazar mesajına cevap "
                "vermeyi unuttun mu? 🤔 Şimdi yazarsan (1. / 2. / 3. şeklinde) "
                "onları da kaydederim."
            )
            set_bekleyen_soru("haftalik_hedef")
        return

    send_message(
        "📊 Haftalık hedeflerinin durumu:\n\n" +
        "\n".join(f"{i+1}. {r['HedefMetni']}" for i, (_, r) in enumerate(bu_haftaki)),
        buttons=[
            [
                {"text": f"{i+1}️⃣ ✅", "callback_data": f"hedef_{row_num}_evet"},
                {"text": f"{i+1}️⃣ ❌", "callback_data": f"hedef_{row_num}_hayir"},
            ]
            for i, (row_num, r) in enumerate(bu_haftaki)
        ],
    )


def hafta_ortasi():
    haftalik_hedef_sorulari_gonder(sessiz_gecerse_hicbir_sey_yapma=False)


def aforizma_kontrol():
    """Her gün RASTGELE bir saatte bir borsa aforizması gönderir (plan
    sadakati, sabır, doğru anı bekleme, acele etmeme temalı). Sabit bir
    cron saati 'rastgele' isteğini karşılamaz - bunun yerine her gün için
    önce rastgele bir HEDEF SAAT belirlenip Durum sekmesine kaydediliyor;
    bu fonksiyon sık aralıklarla (15 dakikada bir, aforizma.yml ile)
    çalışıp o hedef saat geçti mi diye kontrol ediyor - geçtiyse VE bugün
    henüz gönderilmediyse aforizmayı gönderiyor. Böylece bir gün 04:53'te,
    başka bir gün 22:40'ta gelebiliyor - gerçekten öngörülemez."""
    simdi = datetime.datetime.now(TR_TZ)
    bugun = simdi.strftime("%Y-%m-%d")

    hedef_tarih = get_deger("aforizma_hedef_tarih")
    if hedef_tarih != bugun:
        # Bugün için henüz rastgele bir hedef saat belirlenmemiş.
        rastgele_saat = random.randint(0, 23)
        rastgele_dakika = random.randint(0, 59)
        set_deger("aforizma_hedef_tarih", bugun)
        set_deger("aforizma_hedef_saat", f"{rastgele_saat:02d}:{rastgele_dakika:02d}")
        return  # hedef az önce belirlendi, gönderim ileride bir çalıştırmada olacak

    if get_deger("aforizma_son_gonderim") == bugun:
        return  # bugün zaten gönderildi

    hedef_saat_str = get_deger("aforizma_hedef_saat")
    if not hedef_saat_str or ":" not in hedef_saat_str:
        return
    hedef_saat, hedef_dakika = map(int, hedef_saat_str.split(":"))
    hedef_dt = simdi.replace(hour=hedef_saat, minute=hedef_dakika, second=0, microsecond=0)

    if simdi < hedef_dt:
        return  # hedef saat henüz gelmedi

    secilen = aforizma_sec()
    if not secilen:
        return

    send_message(f"💭 \"{secilen['soz']}\"\n— {secilen['yazar']}")
    aforizma_gonderildi_isaretle(secilen["soz"])
    set_deger("aforizma_son_gonderim", bugun)


GOREVLER = {
    "sabah": sabah,
    "aksam": aksam,
    "pazar": pazar,
    "hafta_ortasi": hafta_ortasi,
    "hatirlat": hatirlat,
    "aforizma_kontrol": aforizma_kontrol,
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in GOREVLER:
        print(f"Kullanım: python gonder.py [{'|'.join(GOREVLER.keys())}]")
        sys.exit(1)

    GOREVLER[sys.argv[1]]()
    print(f"Gönderildi: {sys.argv[1]}")


if __name__ == "__main__":
    main()
