"""
[MULTI-AGENT ROL: TOPLAYICI (Collector) — veri kaydetme + sınıflandırma tarafı]
Toplayıcı agent'ının diğer yarısı (soru soran yarı gonder.py'de). Bu dosya,
kullanıcıdan gelen HER TÜRLÜ girdiyi (buton, serbest metin) SLM ile
sınıflandırıp ortak hafızaya (Google Sheets) doğru şekilde yazar. Ayrıca
Koç'un sunduğu önerilere kullanıcı cevabını işleyip Rutinler sekmesini
GÜNCELLER (onay sonrası) - yani Koç'un kararının uygulanma noktası burasıdır.

GitHub Actions'ın repository_dispatch (telegram_update) event'i ile
ANINDA tetiklenir. Cloudflare Worker'ın webhook üzerinden ilettiği
güncellemeyi (buton basımı YA DA serbest metin mesaj) işler.
"""

import json
import os
import re
import datetime


def satirlari_ayikla(text):
    """Serbest metinden madde listesi çıkarır. İki kural birlikte çalışır:
    (1) Eğer mesajda numaralı satır(lar) varsa, SADECE numaralı satırlar
    madde sayılır - başlık/giriş cümlesi elenir.
    (2) Numaralı satır HİÇ yoksa, yine de ':' ile biten kısa bir başlık/
    talimat cümlesi (ör. 'günlük görevlere ekleme yap:') varsa o elenir -
    geri kalan satırlar madde sayılır. Bu ikinci kural olmadan, numarasız
    bir talimat + tek maddelik mesajlarda talimat cümlesinin kendisi de
    yanlışlıkla bir madde sanılıyordu (gerçek bir hata, düzeltildi)."""
    satirlar_ham = [s.strip() for s in text.split("\n") if s.strip()]
    numarali_var = any(re.match(r"^\d+[\.\)\-]", s) for s in satirlar_ham)

    maddeler = []
    for satir in satirlar_ham:
        numarali_mi = re.match(r"^\d+[\.\)\-]?\s*", satir)
        if numarali_var and not numarali_mi:
            continue  # numaralı liste varsa, numarasız satırlar (başlık/giriş) elenir
        if not numarali_var and not numarali_mi and satir.endswith(":") and len(satir) < 60:
            continue  # numara yoksa da, ':' ile biten kısa bir başlık/talimat satırı elenir
        satir = re.sub(r"^\d+[\.\)\-]?\s*", "", satir).strip()
        if satir:
            maddeler.append(satir)
    return maddeler
from common import (
    send_message,
    answer_callback,
    log_to_sheet,
    save_last_update_id,
    get_gorevler_sheet,
    get_haftalik_sheet,
    get_bekleyen_soru,
    set_bekleyen_soru,
    hafta_baslangic_str,
    slm_sorgula,
    turkce_disi_karakter_var_mi,
    update_zaten_islendi_mi,
    update_islendi_isaretle,
    log_slm_karari,
    log_anlasmazlik,
    SLM_MODEL_KALITELI,
    metinden_tarih_cikar,
    guvenli_append_row,
    get_aktif_rutinler,
    get_aktif_haftalik_rutinler,
    get_haftalik_rutin_takip_sheet,
    get_sheet,
    get_rutinler_sheet,
    rutin_serisi_hesapla,
    cevaplanan_rutinler,
    dun_kacirildi_mi,
    get_aforizma_kullanici_sheet,
    KULLANICI_ADI,
    TR_TZ,
)


def bugun_str():
    return datetime.datetime.now(TR_TZ).strftime("%Y-%m-%d")


def process_callback(cq):
    callback_data = cq["data"]
    print(f"[webhook] Buton basıldı: {callback_data}")
    answer_callback(cq["id"])

    if callback_data == "fransizca_evet":
        send_message(
            "Süper! Kaç dakika çalıştın?",
            buttons=[
                [
                    {"text": "5dk", "callback_data": "dk_5"},
                    {"text": "10dk", "callback_data": "dk_10"},
                    {"text": "15dk", "callback_data": "dk_15"},
                    {"text": "20dk+", "callback_data": "dk_20plus"},
                ]
            ],
        )
    elif callback_data == "fransizca_hayir":
        log_to_sheet("Fransızca", "Yapılmadı")
        send_message("Sorun değil, yarın devam edelim 👍")
    elif callback_data.startswith("dk_"):
        dakika = callback_data.replace("dk_", "").replace("plus", "+")
        log_to_sheet("Fransızca", "Yapıldı", f"{dakika} dakika")
        send_message(f"Kaydedildi: {dakika} dakika Fransızca. Tebrikler! 🎉")
    elif callback_data == "hafta_iyi":
        log_to_sheet("Haftalık Kontrol", "İyi gidiyor")
        send_message("Harika, devam! 💪")
    elif callback_data == "hafta_geride":
        log_to_sheet("Haftalık Kontrol", "Geride")
        send_message("Sorun değil, kalan günlerde toparlarız 👍")
    elif callback_data.startswith("rutin_"):
        # Yeni format: rutin_<id>_<YYYY-MM-DD>_evet/hayir/telafi
        # Eski format (bu düzeltmeden önce gönderilmiş, henüz cevaplanmamış
        # butonlar için geriye dönük uyumluluk): rutin_<id>_evet/hayir/telafi
        parcalar = callback_data.split("_")
        sonuc = parcalar[-1]
        if len(parcalar) >= 3 and re.match(r"^\d{4}-\d{2}-\d{2}$", parcalar[-2]):
            tarih = parcalar[-2]
            rutin_id = "_".join(parcalar[1:-2])
        else:
            tarih = None  # eski format - log_to_sheet bugünü kullanır
            rutin_id = "_".join(parcalar[1:-1])

        rutin = next((r for r in get_aktif_rutinler() if r["id"] == rutin_id), None)
        isim = rutin["isim"] if rutin else rutin_id
        if sonuc == "evet":
            log_to_sheet(isim, "Yapıldı", tarih=tarih)
            send_message(f"✅ '{isim}' kaydedildi. Tebrikler!")
        elif sonuc == "hayir":
            log_to_sheet(isim, "Yapılmadı", tarih=tarih)
            send_message(f"Sorun değil, '{isim}' için yarın devam edelim 👍")
        elif sonuc == "telafi":
            # Kullanıcı hem bugünkü kendi rutinini hem dünkü eksiği
            # tamamladığını bildiriyor. Bugün "Yapıldı" (tam, gerçek
            # anlamda tamamlanmış) sayılır; dün ise "Telafi" (nötr,
            # kaçırma da sayılmaz) olarak işaretlenir - önceden sadece
            # bugüne "Telafi" yazılıyordu, dün hiç düzeltilmiyordu.
            bugun_referans = tarih or bugun_str()
            try:
                bugun_tarih_obj = datetime.datetime.strptime(bugun_referans, "%Y-%m-%d").date()
                dun_str_deger = (bugun_tarih_obj - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
            except ValueError:
                dun_str_deger = None

            log_to_sheet(isim, "Yapıldı", tarih=bugun_referans)
            if dun_str_deger:
                log_to_sheet(isim, "Telafi", "ertesi gün telafi edildi", tarih=dun_str_deger)
            send_message(f"🔁 Harika, '{isim}' bugün tamamlandı, dünkü eksik de telafi edildi olarak kaydedildi!")
    elif callback_data.startswith("koc_duraklat_"):
        # format: koc_duraklat_<id>_evet / koc_duraklat_<id>_hayir
        parcalar = callback_data.split("_")
        sonuc = parcalar[-1]
        rutin_id = "_".join(parcalar[2:-1])

        rutin = next((r for r in get_aktif_rutinler() if r["id"] == rutin_id), None)
        isim = rutin["isim"] if rutin else rutin_id
        _, miss_streak = rutin_serisi_hesapla(isim)

        if sonuc == "evet":
            ws = get_rutinler_sheet()
            rows = ws.get_all_values()
            bulundu = False
            for i, row in enumerate(rows[1:], start=2):
                if row[0] == rutin_id:
                    ws.update_cell(i, 4, "FALSE")
                    bulundu = True
                    break
            if bulundu:
                log_to_sheet(f"Koç kararı: {rutin_id}", "Duraklatıldı")
            durum_metni = "duraklatmayı kabul etti" if bulundu else "duraklatmak istedi ama bir hata oldu"
        else:
            durum_metni = "devam etmeyi seçti (duraklatmadı)"

        prompt = (
            "Sen bir verimlilik koçu botusun (adın Poke). Kullanıcı "
            f"'{isim}' rutinini {miss_streak} gündür kaçırıyordu, sen ona "
            f"duraklatmayı önermiştin, o da {durum_metni}. "
            "Ona kısa (2-3 cümle), destekleyici, pratik bir tavsiye ver - "
            "yargılamadan, samimi bir dille. SADECE mesajı yaz, başka "
            "açıklama ekleme."
        )
        try:
            cevap_mesaji = slm_sorgula(prompt)
            if turkce_disi_karakter_var_mi(cevap_mesaji):
                raise ValueError("dil kayması")
        except Exception as e:
            print(f"SLM hatası (koç cevabı): {e}")
            cevap_mesaji = (
                "🧑‍🏫 Tamam, kaydettim." if sonuc == "evet" else "🧑‍🏫 Tamam, aynen devam ediyoruz 💪"
            )

        send_message(cevap_mesaji)

    elif callback_data.startswith("gorev_"):
        # format: gorev_<satirNo>_evet / gorev_<satirNo>_hayir
        _, satir_no, sonuc = callback_data.split("_")
        ws = get_gorevler_sheet()
        satir_no = int(satir_no)
        gorev_tarihi = ws.cell(satir_no, 1).value
        gorev_metni = ws.cell(satir_no, 3).value
        durum = "Yapıldı" if sonuc == "evet" else "Yapılmadı"
        ws.update_cell(satir_no, 4, durum)
        log_to_sheet(gorev_metni, durum, tarih=gorev_tarihi)
        if sonuc == "evet":
            send_message(f"✅ '{gorev_metni}' kaydedildi. Tebrikler!")
        else:
            send_message(f"Sorun değil, '{gorev_metni}' için yarın devam edelim 👍")

    elif callback_data.startswith("hedef_"):
        # format: hedef_<satirNo>_evet / hedef_<satirNo>_hayir
        _, satir_no, sonuc = callback_data.split("_")
        ws = get_haftalik_sheet()
        satir_no = int(satir_no)
        hedef_metni = ws.cell(satir_no, 2).value
        durum = "Yapıldı" if sonuc == "evet" else "Yapılmadı"
        ws.update_cell(satir_no, 3, durum)
        if sonuc == "evet":
            send_message(f"✅ '{hedef_metni}' yolunda olarak kaydedildi. Devam!")
        else:
            send_message(f"Not aldım, '{hedef_metni}' geride kalmış — toparlamaya çalış 💪")

    elif callback_data.startswith("haftarutin_"):
        # format: haftarutin_<satirNo>_evet / haftarutin_<satirNo>_hayir
        _, satir_no, sonuc = callback_data.split("_")
        ws = get_haftalik_rutin_takip_sheet()
        satir_no = int(satir_no)
        rutin_isim = ws.cell(satir_no, 3).value
        durum = "Yapıldı" if sonuc == "evet" else "Yapılmadı"
        ws.update_cell(satir_no, 4, durum)
        if sonuc == "evet":
            send_message(f"✅ '{rutin_isim}' bu hafta için tamamlandı. Tebrikler!")
        else:
            send_message(f"Sorun değil, '{rutin_isim}' için hafta bitmeden hâlâ vaktin var 👍")


def _sorguyu_cevapla(text):
    """Kullanıcı bir şey sorguladığında GERÇEK veriyi Sheets'ten okuyup,
    DOĞRUDAN Python'da (SLM'e yazdırmadan) net bir cevap verir - SLM
    serbest metin üretirken yazım hatası yapabiliyordu, deterministik
    formatlama bunu ortadan kaldırıyor. Dört sorgu türünü ayırt eder:
    seri/streak soruları, HAFTALIK KATEGORİ rutinlerinin bu haftaki
    durumu, günlük rutinlerin haftalık yüzdesi, ve varsayılan (bugün)."""
    metin_kucuk = text.lower()

    if any(k in metin_kucuk for k in ["seri", "streak", "kaç gündür"]):
        _seri_sorusunu_cevapla()
        return

    # "Haftalık rutin" tam ifadesi VEYA doğrudan bir haftalık rutinin adı
    # (Oda tozu alma, Uzun metraj izlence, Making Music gibi - dinamik
    # olarak sheet'ten çekiliyor, rutin değişirse otomatik güncel kalır)
    # VEYA "düzenli/tekrarlayan iş" tarzı doğal eşanlamlılar - bunların
    # HERHANGİ biri, GÜNLÜK rutinlerin haftalık yüzdesinden (aşağıdaki
    # genel 'hafta' yakalayıcısı) AYRI, kendi kategorisi olan
    # haftalık-TEKRARLI rutinlerin O HAFTAKİ durumunu sorduğu anlamına
    # gelir. Kullanıcı "sadece dar bir ifadeyi mi yakaladın" diye haklı
    # bir soru sordu - bu yüzden ağ genişletildi (rutin isimleri +
    # birkaç doğal eşanlamlı), ama HÂLÂ tamamen deterministik/kelime
    # tabanlı - kök semantik anlama sorununu (bkz. README'deki "Bekleyen
    # Geliştirmeler") çözmüyor, sadece daha geniş, hâlâ %100 öngörülebilir
    # bir güvenli liman sağlıyor.
    haftalik_rutin_isimleri_kucuk = [r["isim"].lower() for r in get_aktif_haftalik_rutinler()]
    haftalik_rutin_esanlamlilar = [
        "haftalık rutin", "haftalik rutin",
        "düzenli yaptığım", "düzenli olarak yaptığım",
        "her hafta yaptığım", "her hafta düzenli",
        "tekrarlayan iş", "tekrarlayan görev", "tekrarlayan iş(ler)",
    ]
    if (any(k in metin_kucuk for k in haftalik_rutin_esanlamlilar)
            or any(isim in metin_kucuk for isim in haftalik_rutin_isimleri_kucuk)):
        _haftalik_rutin_durumu_cevapla()
        return

    # "Bu haftaki HEDEFLERİM/GÖREVLERİM" — HaftalikHedefler sekmesindeki
    # (checkbox'lı, Yolunda/Geride) haftalık hedefleri sorar. Önceden bu
    # dal HİÇ YOKTU: "hedef" kelimesi metinde geçmezse ("bu haftaki
    # görevlerimi hatırlatır mısın" gibi, kullanıcı "hedef" değil "görev"
    # dediğinde) direkt bir alttaki genel 'hafta' yakalayıcısına düşüyor
    # ve GÜNLÜK RUTİNLERİN 7 günlük yüzdesini basıyordu - kullanıcının hiç
    # istemediği bir cevap. "hedef" VEYA "görev" + "hafta" birlikteliği
    # artık doğrudan haftalık hedeflere yönleniyor; sadece "hedef"
    # kelimesini arayan eski daraltıcı kontrol kaldırıldı.
    if "hafta" in metin_kucuk and ("hedef" in metin_kucuk or "görev" in metin_kucuk or "gorev" in metin_kucuk):
        _haftalik_hedef_durumu_cevapla()
        return

    if "hafta" in metin_kucuk:
        _haftalik_ozet_sorusunu_cevapla()
        return

    # 'Geçmişten kalan TÜM bekleyenler' - belirli bir güne değil, TÜM
    # tarihlere yayılan sorgular. _bugunku_durumu_cevapla tek bir günü
    # hedefler (metinden_tarih_cikar bulamazsa varsayılan bugün'e düşer) -
    # bu kalıp gerçek bir olayda "geçmişten kalan tüm bekliyor statüsündeki
    # günlük görevlerimi tarihleriyle sorgular mısın" mesajını yanlışlıkla
    # sadece bugüne indirgeyip cevapladı. Burada net bir 'tüm/hepsi/geçmiş'
    # sinyali VE belirli bir tarih YOKSA, tarihler arası özel fonksiyona
    # yönlendiriyoruz.
    #
    # UYARI - AYNI HATA İKİNCİ KEZ YAŞANDI: sabit kalıp listesi ("geçmişten
    # kalan", "tüm bekleyen" vb.) sadece test ettiğim TEK cümleyi kapsıyordu
    # - kullanıcı doğal bir şekilde "bugünden önceki günlerde..." dediğinde
    # hiçbiri eşleşmedi, sessizce bugüne düştü. Sabit kalıp listeleri bu tür
    # açık uçlu Türkçe ifadeler için doğası gereği EKSİK kalıyor (aynı
    # "neler"in sorgu_kaliplari'nda unutulması gibi). Bu yüzden artık tek
    # tek kalıp saymak yerine, "önceki/geçmiş" + "gün(ler)" birlikteliğini
    # yakalayan bir REGEX de var - "önceki günlerde", "geçmiş günlerdeki",
    # "bugünden önceki günler" gibi pek çok doğal varyasyonu tek seferde
    # kapsıyor, tek tek cümle ezberlemek yerine.
    tum_gecmis_kaliplari = [
        "geçmişten kalan", "tüm bekleyen", "bütün bekleyen",
        "tüm görevlerim", "bütün görevlerim", "geçmiş görevlerim",
        "hepsini", "tüm geçmiş", "tüm zamanlarda", "bütün zamanlarda",
    ]
    gecmis_gun_regex = re.search(r"\b(öncek\w*|geçmiş\w*)\s+g[üu]n", metin_kucuk)
    if (any(k in metin_kucuk for k in tum_gecmis_kaliplari) or gecmis_gun_regex) and metinden_tarih_cikar(text) is None:
        _tum_bekleyen_gorevleri_cevapla()
        return

    _bugunku_durumu_cevapla(text)


def _haftalik_hedef_durumu_cevapla():
    """Kullanıcının BU HAFTA için kaydettiği HaftalikHedefler sekmesindeki
    (Pazar günü '1./2./3.' şeklinde yazdığı, Yolunda/Geride ile işaretlenen)
    hedeflerin durumunu gösterir. _haftalik_ozet_sorusunu_cevapla (günlük
    rutinlerin 7 günlük yüzdesi) ve _haftalik_rutin_durumu_cevapla (ayrı bir
    HAFTALIK RUTİN kategorisi - Oda tozu alma vb.) ile KARIŞTIRILMASIN - bu
    üçü Sheets'te üç ayrı sekmeye (Takip, HaftalikRutinTakip, HaftalikHedefler)
    karşılık gelen üç farklı veri. 'Bekliyor' durumundaki hedefler için
    TIKLANABİLİR butonlar ekler - `hedef_<satır>_evet/hayir`
    (gonder.py'nin haftalik_hedef_sorulari_gonder'inde ve process_callback'te
    ZATEN kullanılan aynı format, satır bazlı) - sıfırdan yazmaya gerek yok."""
    ws = get_haftalik_sheet()
    hafta = hafta_baslangic_str()
    rows = ws.get_all_records()

    satirlar = []
    bekleyenler = []  # (satir_no, metin) - sadece 'Bekliyor' durumundakiler
    for i, r in enumerate(rows):
        if r.get("HaftaBaslangic") != hafta:
            continue
        durum = r.get("Durum")
        metin = r.get("HedefMetni", "")
        satir_no = i + 2  # header satırı + 1-index
        if durum == "Yolunda":
            isaret = "✅"
        elif durum == "Geride":
            isaret = "❌"
        elif durum == "Bekliyor":
            isaret = "⏳"
            bekleyenler.append((satir_no, metin))
        else:
            isaret = "⏳"
            bekleyenler.append((satir_no, metin))
        satirlar.append(f"{isaret} {metin}")

    if not satirlar:
        send_message(
            "Bu hafta için henüz kaydedilmiş bir haftalık hedef bulamadım — "
            "Pazar mesajına cevap vermeyi unuttun mu? 🤔 Şimdi yazarsan "
            "(1. / 2. / 3. şeklinde) onları da kaydederim."
        )
        set_bekleyen_soru("haftalik_hedef")
        return

    mesaj = "Bu haftaki hedeflerinin durumu:\n" + "\n".join(satirlar)

    if bekleyenler:
        buton_satirlari = [
            [
                {"text": f"{i+1}️⃣ ✅", "callback_data": f"hedef_{satir_no}_evet"},
                {"text": f"{i+1}️⃣ ❌", "callback_data": f"hedef_{satir_no}_hayir"},
            ]
            for i, (satir_no, _) in enumerate(bekleyenler)
        ]
        send_message(mesaj, buttons=buton_satirlari)
    else:
        send_message(mesaj)


def _haftalik_rutin_durumu_cevapla():
    """Kullanıcının HAFTALIK KATEGORİ rutinlerinin (günlük DEĞİL - ör.
    'Oda tozu alma', 'Uzun metraj izlence', 'Making Music') BU HAFTAKİ
    durumunu gösterir. _haftalik_ozet_sorusunu_cevapla ile KARIŞTIRILMASIN
    - o, günlük rutinlerin (Fransızca, telefonsuzluk vb.) SON 7 GÜNLÜK
    yüzdesini gösterir; bu fonksiyon ise ayrı bir kategorinin BU HAFTAKİ
    ham durumunu (Yapıldı/Bekliyor/Yapılmadı) gösterir. 'Bekliyor'
    durumundaki olanlar için TIKLANABİLİR butonlar ekliyor -
    `haftarutin_<satır>_evet/hayir` (process_callback'te ve gonder.py'nin
    otomatik hatırlatmasında ZATEN kullanılan aynı format, satır bazlı) -
    günlük tarafta yapılan _kalan_durumu_interaktif_gonder ile aynı fikir."""
    haftalik_rutinler = get_aktif_haftalik_rutinler()
    if not haftalik_rutinler:
        send_message("Tanımlı bir haftalık rutin yok.")
        return

    ws = get_haftalik_rutin_takip_sheet()
    hafta = hafta_baslangic_str()
    rows = ws.get_all_values()

    satirlar = []
    bekleyenler = []  # (satir_no, isim) - sadece 'Bekliyor' durumundakiler
    for i, row in enumerate(rows[1:], start=1):
        if len(row) < 4 or row[0] != hafta:
            continue
        isim, durum = row[2], row[3]
        if durum == "Yapıldı":
            isaret = "✅"
        elif durum == "Yapılmadı":
            isaret = "❌"
        else:
            isaret = "⏳"
            bekleyenler.append((i + 1, isim))  # +1: header satırı + 1-index
        satirlar.append(f"{isaret} {isim}")

    if not satirlar:
        send_message("Bu hafta için henüz kayıtlı bir haftalık rutin durumu yok.")
        return

    mesaj = "Bu haftaki (haftalık) rutin durumun:\n" + "\n".join(satirlar)

    if bekleyenler:
        buton_satirlari = [
            [
                {"text": f"{i+1}️⃣ ✅", "callback_data": f"haftarutin_{satir_no}_evet"},
                {"text": f"{i+1}️⃣ ❌", "callback_data": f"haftarutin_{satir_no}_hayir"},
            ]
            for i, (satir_no, _) in enumerate(bekleyenler)
        ]
        send_message(mesaj, buttons=buton_satirlari)
    else:
        send_message(mesaj)


def _seri_sorusunu_cevapla():
    rutinler = get_aktif_rutinler()
    if not rutinler:
        send_message("Henüz tanımlı bir rutin yok.")
        return
    satirlar = []
    for r in rutinler:
        streak, miss_streak = rutin_serisi_hesapla(r["isim"])
        if streak > 0:
            satirlar.append(f"🔥 {r['isim']}: {streak} gündür kesintisiz")
        elif miss_streak > 0:
            satirlar.append(f"⚠️ {r['isim']}: {miss_streak} gündür kaçırılıyor")
        else:
            satirlar.append(f"• {r['isim']}: aktif bir seri yok")
    send_message("Rutin serilerin:\n" + "\n".join(satirlar))


def _haftalik_ozet_sorusunu_cevapla():
    rutinler = get_aktif_rutinler()
    ws = get_sheet()
    rows = ws.get_all_records()
    bugun = datetime.datetime.now(TR_TZ).date()
    sinir = bugun - datetime.timedelta(days=6)

    satirlar = []
    for r in rutinler:
        toplam = 0
        yapilan = 0
        for row in rows:
            if row.get("Görev") != r["isim"]:
                continue
            try:
                tarih = datetime.datetime.strptime(row["Tarih"], "%Y-%m-%d").date()
            except (ValueError, KeyError):
                continue
            if tarih < sinir:
                continue
            toplam += 1
            if row["Durum"] in ("Yapıldı", "Telafi"):
                yapilan += 1
        if toplam:
            satirlar.append(f"• {r['isim']}: {yapilan}/{toplam} gün")
        else:
            satirlar.append(f"• {r['isim']}: bu hafta hiç kayıt yok")

    send_message("Bu haftaki (son 7 gün) rutin durumun:\n" + "\n".join(satirlar))


_AY_ISIMLERI_TERS = {
    1: "Ocak", 2: "Şubat", 3: "Mart", 4: "Nisan", 5: "Mayıs", 6: "Haziran",
    7: "Temmuz", 8: "Ağustos", 9: "Eylül", 10: "Ekim", 11: "Kasım", 12: "Aralık",
}


def _gun_ifadesi(tarih):
    """YYYY-MM-DD -> kullanıcıya doğal gelecek bir ifade ('Bugün', 'Dün',
    ya da '22 Temmuz'). Mesajlarda '{ifade} için ...' kalıbıyla kullanılır."""
    bugun = bugun_str()
    dun = (datetime.datetime.now(TR_TZ).date() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    if tarih == bugun:
        return "Bugün"
    if tarih == dun:
        return "Dün"
    try:
        d = datetime.datetime.strptime(tarih, "%Y-%m-%d").date()
        return f"{d.day} {_AY_ISIMLERI_TERS[d.month]}"
    except (ValueError, KeyError):
        return tarih


def _gun_verisini_getir(tarih):
    """Belirli bir tarih (YYYY-MM-DD) için o güne ait görev ve rutin
    takip satırlarını döndürür - _bugunku_durumu_cevapla'nın hem 'bugün'
    hem geçmiş bir tarih için kullanabileceği ortak veri katmanı."""
    ws_gorev = get_gorevler_sheet()
    gorevler = [r for r in ws_gorev.get_all_records() if r.get("Tarih") == tarih]

    rutin_isimleri = {r["isim"] for r in get_aktif_rutinler()}
    ws_takip = get_sheet()
    takip = [
        r for r in ws_takip.get_all_records()
        if r.get("Tarih") == tarih and r.get("Görev") in rutin_isimleri
    ]
    return gorevler, takip


def _kalan_durumu_interaktif_gonder(hedef_tarih, ifade, erken_saat_varsayimi=False):
    """Belirli bir tarih için HENÜZ İŞARETLENMEMİŞ (Bekliyor/cevaplanmamış)
    görev ve rutinleri, aksam()/rutin_sorulari_gonder() (gonder.py) ile
    BİREBİR AYNI buton formatını kullanarak İKİ AYRI, tıklanabilir mesaj
    hâlinde gönderir - kullanıcı buradan direkt işaretleyebilsin, sadece
    okuyup Sheets'e elle gitmek zorunda kalmasın diye. Callback'ler zaten
    tarihe duyarlı tasarlandığı için (rutin_<id>_<tarih>_..., gorev_<satır>
    satır bazlı) bu, herhangi bir GEÇMİŞ tarih için de sorunsuz çalışır -
    process_callback'te hiçbir değişiklik gerekmedi.
    Dönüş: en az bir mesaj gönderildiyse True, gönderilecek bir şey
    (hiçbir şey Bekliyor/cevapsız değilse) yoksa False."""
    on_not = (
        f"(Henüz uyumadığını düşünüp {ifade.lower()}kü listeni gösteriyorum - "
        "başka bir günü kastettiysen tarihi söyle yeter.)\n\n"
        if erken_saat_varsayimi else ""
    )
    bir_sey_gonderildi = False

    # --- Ad-hoc günlük görevler (hâlâ 'Bekliyor' olanlar) ---
    ws_gorev = get_gorevler_sheet()
    rows = ws_gorev.get_all_records()
    bekleyen_gorevler = [
        (i + 2, r) for i, r in enumerate(rows)  # +2: başlık satırı + 1-index
        if r.get("Tarih") == hedef_tarih and r.get("Durum") == "Bekliyor"
    ]
    if bekleyen_gorevler:
        satir_metinleri = [f"{i+1}. {r['GorevMetni']}" for i, (_, r) in enumerate(bekleyen_gorevler)]
        buton_satirlari = [
            [
                {"text": f"{i+1}️⃣ ✅", "callback_data": f"gorev_{row_num}_evet"},
                {"text": f"{i+1}️⃣ ❌", "callback_data": f"gorev_{row_num}_hayir"},
            ]
            for i, (row_num, r) in enumerate(bekleyen_gorevler)
        ]
        mesaj = on_not + f"📋 {ifade} için kalan görevlerin:\n\n" + "\n".join(satir_metinleri)
        send_message(mesaj, buttons=buton_satirlari)
        on_not = ""  # ikinci mesajda tekrar etmesin
        bir_sey_gonderildi = True

    # --- Rutinler (o tarih için henüz cevaplanmamış olanlar) ---
    rutinler = get_aktif_rutinler()
    cevaplanan = cevaplanan_rutinler(hedef_tarih)
    bekleyen_rutinler = [r for r in rutinler if r["isim"] not in cevaplanan]
    if bekleyen_rutinler:
        satir_metinleri = [f"{i+1}. {r['soru']}" for i, r in enumerate(bekleyen_rutinler)]
        buton_satirlari = []
        for i, r in enumerate(bekleyen_rutinler):
            butonlar = [
                {"text": f"{i+1}️⃣ ✅", "callback_data": f"rutin_{r['id']}_{hedef_tarih}_evet"},
                {"text": f"{i+1}️⃣ ❌", "callback_data": f"rutin_{r['id']}_{hedef_tarih}_hayir"},
            ]
            # Telafi (🔁) seçeneği sadece BUGÜN için anlamlı - 'bugün hem
            # kendi rutinimi hem dünkü eksiği tamamladım' kavramı, geçmiş
            # bir tarih sorgulanırken karışıklık yaratır, o yüzden eklenmiyor.
            if hedef_tarih == bugun_str() and r.get("telafi_edilebilir", True) and dun_kacirildi_mi(r["isim"], hedef_tarih):
                butonlar.append({"text": f"{i+1}️⃣ 🔁", "callback_data": f"rutin_{r['id']}_{hedef_tarih}_telafi"})
            buton_satirlari.append(butonlar)
        mesaj = on_not + f"🔁 {ifade} için kalan rutinlerin:\n\n" + "\n".join(satir_metinleri)
        send_message(mesaj, buttons=buton_satirlari)
        bir_sey_gonderildi = True

    return bir_sey_gonderildi


def _tum_bekleyen_gorevleri_cevapla():
    """'Geçmişten kalan tüm bekleyen günlük görevlerim' tarzı sorguları
    karşılar - _bugunku_durumu_cevapla'nın tersine TEK bir güne değil,
    Sheets'teki TÜM tarihlere yayılan 'Bekliyor' durumundaki ad-hoc
    günlük görevleri bulur, tarihe göre gruplayıp TEK bir tıklanabilir
    mesajda gönderir (gorev_<satır> callback'i satır bazlı çalıştığı için
    farklı tarihlerden gelen görevler aynı mesajda sorunsuz karışabilir)."""
    ws = get_gorevler_sheet()
    rows = ws.get_all_records()
    bekleyenler = [
        (i + 2, r) for i, r in enumerate(rows)
        if r.get("Durum") == "Bekliyor"
    ]

    if not bekleyenler:
        send_message("Bekleyen (henüz işaretlenmemiş) hiç günlük görevin yok - hepsi güncel! 🎉")
        return

    bekleyenler.sort(key=lambda x: x[1].get("Tarih", ""))

    MAKS_GOSTERILEN = 25
    fazlasi_var = len(bekleyenler) > MAKS_GOSTERILEN
    gosterilecekler = bekleyenler[:MAKS_GOSTERILEN]

    satirlar = []
    buton_satirlari = []
    mevcut_tarih = None
    for i, (row_num, r) in enumerate(gosterilecekler):
        tarih = r.get("Tarih", "")
        if tarih != mevcut_tarih:
            mevcut_tarih = tarih
            satirlar.append(f"\n📅 {_gun_ifadesi(tarih)} ({tarih}):")
        satirlar.append(f"{i+1}. {r.get('GorevMetni', '')}")
        buton_satirlari.append([
            {"text": f"{i+1}️⃣ ✅", "callback_data": f"gorev_{row_num}_evet"},
            {"text": f"{i+1}️⃣ ❌", "callback_data": f"gorev_{row_num}_hayir"},
        ])

    baslik = f"Geçmişten kalan {len(bekleyenler)} bekleyen günlük görevin var:"
    if fazlasi_var:
        baslik += f" (ilk {MAKS_GOSTERILEN} tanesi gösteriliyor, tarih belirterek daralt.)"

    send_message(baslik + "\n" + "\n".join(satirlar), buttons=buton_satirlari)


def _bugunku_durumu_cevapla(text):
    """Hem 'bugünkü durumum ne' hem 'dün'/'22 Temmuz'dan kalan görevlerim'
    gibi GEÇMİŞ bir tarihe ait sorguları kapsar. Tarih mesajda açıkça
    belirtilmemişse VE bugün için hiçbir kayıt yoksa VE saat hâlâ gece
    yarısından sonraki erken saatlerdeyse (00:00-05:00), kullanıcı
    muhtemelen henüz uyumadı ve zihinsel olarak hâlâ bir önceki günü
    kastediyor - bu durumda DÜN'e otomatik düşülür, ama bu SESSİZCE
    yapılmaz: hangi günün gösterildiği cevapta her zaman açıkça belirtilir."""
    tarih_belirtilmis = metinden_tarih_cikar(text)
    hedef_tarih = tarih_belirtilmis or bugun_str()
    gorevler, takip = _gun_verisini_getir(hedef_tarih)

    erken_saat_varsayimi = False
    if not tarih_belirtilmis and not gorevler and not takip:
        simdi = datetime.datetime.now(TR_TZ)
        if simdi.hour < 5:
            dun_tarih = (simdi.date() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
            gorevler_dun, takip_dun = _gun_verisini_getir(dun_tarih)
            if gorevler_dun or takip_dun:
                hedef_tarih = dun_tarih
                gorevler, takip = gorevler_dun, takip_dun
                erken_saat_varsayimi = True

    ifade = _gun_ifadesi(hedef_tarih)

    if not gorevler and not takip:
        send_message(f"{ifade} için henüz kayıtlı bir görev ya da rutin durumu yok.")
        return

    # Kullanıcı sadece eksikleri mi soruyor, yoksa genel durumu mu?
    eksik_kelimeler = ["yapmadığ", "yapmadık", "kaçır", "eksik", "tamamlamadığ", "unuttuğ"]
    sadece_eksikler = any(k in text.lower() for k in eksik_kelimeler)

    if not sadece_eksikler:
        # Varsayılan (genel durum) sorgusunda: sadece OKUNAN düz metin
        # yerine, henüz işaretlenmemiş öğeleri TIKLANABİLİR şekilde gönder.
        # Her şey zaten cevaplanmışsa (gönderilecek bir şey yoksa), aşağıdaki
        # düz-metin tam özet moduna düşülür - o zaten iyi bir "geçmişe
        # bakış" görünümü sağlıyor.
        if _kalan_durumu_interaktif_gonder(hedef_tarih, ifade, erken_saat_varsayimi):
            return

    satirlar = []
    for r in takip:
        if sadece_eksikler and r["Durum"] != "Yapılmadı":
            continue
        if r["Durum"] == "Yapıldı":
            isaret = "✅"
        elif r["Durum"] == "Telafi":
            isaret = "🔁"
        else:
            isaret = "❌"
        satirlar.append(f"{isaret} {r['Görev']}")
    for r in gorevler:
        if sadece_eksikler and r["Durum"] != "Bekliyor":
            continue
        if r["Durum"] == "Yapıldı":
            isaret = "✅"
        elif r["Durum"] == "Yapılmadı":
            isaret = "❌"
        else:
            isaret = "⏳"
        satirlar.append(f"{isaret} {r['GorevMetni']}")

    if not satirlar:
        if sadece_eksikler:
            send_message(f"Harika, {ifade.lower()} için kaçırdığın bir şey görünmüyor! 🎉")
        else:
            send_message(f"{ifade} için henüz kayıtlı bir görev ya da rutin durumu yok.")
        return

    on_not = (
        f"(Henüz uyumadığını düşünüp {ifade.lower()}kü listeni gösteriyorum - "
        "başka bir günü kastettiysen tarihi söyle yeter.)\n\n"
        if erken_saat_varsayimi else ""
    )
    baslik = f"{ifade} için henüz yapmadıkların:" if sadece_eksikler else f"{ifade} için durumun:"
    send_message(on_not + f"{baslik}\n" + "\n".join(satirlar))


def _aforizma_ekle_isle(text):
    """Kullanıcı kendi aforizmasını ekliyor. Bu, SLM'e HİÇ sorulmadan,
    tamamen deterministik işleniyor - bu oturumda defalarca gördüğümüz
    gibi, yeni bir SLM kategorisi eklemek kırılgan olabiliyor; burada
    kalıp yeterince dar ve net ('aforizma' + 'ekle/kaydet' kelimesi) ki
    hiç risk almaya gerek yok."""
    tirnak_ici = re.findall(r'["\u201c\u201d]([^"\u201c\u201d]+)["\u201c\u201d]', text)
    if not tirnak_ici:
        send_message(
            "Eklemek istediğin sözü tırnak içinde yazar mısın? Ör: "
            "aforizma ekle: \"sabırla oturmak her şeyden değerlidir\" - yazar adı"
        )
        return
    soz = tirnak_ici[0].strip()

    yazar_match = (
        re.search(r'["\u201c\u201d]\s*[-–—]\s*(.+)$', text)
        or re.search(r'yazar[:\s]+([^\n]+)$', text, re.IGNORECASE)
    )
    yazar = yazar_match.group(1).strip() if yazar_match else "Kullanıcı"

    ws = get_aforizma_kullanici_sheet()
    guvenli_append_row(ws, [soz, yazar, bugun_str()])
    send_message(f"Eklendi: \"{soz}\" — {yazar}. Zaman zaman diğer sözlerle birlikte karşına çıkacak. 💭")


def process_message(message):
    text = message.get("text", "").strip()
    if not text:
        return

    metin_kucuk = text.lower()
    if "aforizma" in metin_kucuk and ("ekle" in metin_kucuk or "kaydet" in metin_kucuk):
        _aforizma_ekle_isle(text)
        return

    bekleyen = get_bekleyen_soru()
    _siniflandir_ve_isle(text, bekleyen)


_turkce_disi_karakter_var_mi = turkce_disi_karakter_var_mi


BEKLEYEN_ACIKLAMA = {
    "gunluk_gorev": "sabah sorduğum 'bugün ne yapacaksın' sorusu",
    "haftalik_hedef": "pazar günü sorduğum 'bu hafta hedeflerin ne' sorusu",
    "bosa_vakit": "akşam sorduğum 'bugün ne kadar boşa vakit geçirdin' sorusu",
}


def _en_iyi_gorev_eslesmesini_bul(arama_metni, tarih=None):
    """arama_metni ile GunlukGorevler'deki (SADECE Bekliyor/Süresi Doldu
    durumundaki - zaten Yapıldı olan bir şeyi tekrar 'bulup' bozmayalım)
    satırlar arasında en iyi eşleşmeyi arar. Üç aşamalı, temkinli bir
    yaklaşım: (1) tam eşleşme, (2) biri diğerini kapsıyor mu, (3) kelime
    örtüşme oranı - SADECE yeterince güvenli VE tek bir aday varsa kabul
    edilir. Belirsizse ASLA tahmin etmez, None döner - yanlış bir görevi
    'yapıldı' işaretlemek, hiç işaretlememekten daha kötü bir hata."""
    ws = get_gorevler_sheet()
    rows = ws.get_all_records()
    adaylar = [
        i for i, r in enumerate(rows)
        if r.get("Durum") in ("Bekliyor", "Süresi Doldu")
        and (tarih is None or r.get("Tarih") == tarih)
    ]
    if not adaylar:
        return None

    arama_kucuk = arama_metni.lower().strip()

    for i in adaylar:
        if rows[i]["GorevMetni"].lower().strip() == arama_kucuk:
            return (i + 2, rows[i])

    icerenler = [
        i for i in adaylar
        if arama_kucuk in rows[i]["GorevMetni"].lower()
        or rows[i]["GorevMetni"].lower() in arama_kucuk
    ]
    if len(icerenler) == 1:
        return (icerenler[0] + 2, rows[icerenler[0]])

    def _skor(satir_metni):
        a = set(arama_kucuk.split())
        b = set(satir_metni.lower().split())
        if not a or not b:
            return 0
        return len(a & b) / len(a | b)

    skorlar = sorted(((_skor(rows[i]["GorevMetni"]), i) for i in adaylar), reverse=True)
    if skorlar and skorlar[0][0] >= 0.6:
        if len(skorlar) == 1 or skorlar[0][0] - skorlar[1][0] >= 0.2:
            i = skorlar[0][1]
            return (i + 2, rows[i])

    return None


def _gecmis_gorev_tamamla_isle(text):
    """Kullanıcı geçmişte eklediği ad-hoc bir günlük görevi aslında
    tamamladığını bildirdiğinde çağrılır - önceki bir oturumda 'Süresi
    Doldu' bildirimine 'gerçekten yaptıysan söyle, düzeltirim' diye söz
    verilmişti ama bunu gerçekten yapan bir mekanizma hiç kurulmamıştı;
    bu fonksiyon o sözü tutuyor. Tırnak içi varsa (en güvenilir) onu, yoksa
    mesajın tamamını arama anahtarı olarak kullanır; tarih belirtilmişse
    önce o tarihe daraltır, bulamazsa tarihsiz tekrar dener."""
    tirnak_ici = re.findall(r'["\u201c\u201d]([^"\u201c\u201d]+)["\u201c\u201d]', text)
    tarih = metinden_tarih_cikar(text)
    arama_metni = tirnak_ici[0] if tirnak_ici else text

    eslesme = _en_iyi_gorev_eslesmesini_bul(arama_metni, tarih)
    if eslesme is None and tarih is not None:
        eslesme = _en_iyi_gorev_eslesmesini_bul(arama_metni, None)

    if eslesme is None:
        send_message(
            "Hangi görevi kastettiğini tam olarak eşleştiremedim - görevin "
            "adını tırnak içinde birebir (ya da çok yakın) yazar mısın? "
            "Ör: \"görev metni\" yapmıştım."
        )
        return

    satir_no, satir = eslesme
    ws = get_gorevler_sheet()
    ws.update_cell(satir_no, 4, "Yapıldı")
    send_message(f"✅ '{satir['GorevMetni']}' ({satir['Tarih']}) görevini yaptın olarak işaretledim, düzelttim!")


def _gunluk_gorev_isle(text):
    """Hem sabah tam liste akışını ('bugünkü görevlerim: 1) ... 2) ...')
    hem de gün içinde tek/az sayıda ad-hoc ekleme kalıbını ('günlük
    görevlere ekleme yap: X') kapsar. Öncelik: (1) tırnak içi - en
    güvenilir, (2) numaralı/çok satırlı liste, (3) tek satırlık 'ekle:
    X' türü talimat cümlelerinde ':' sonrasını almak - AYNI desen
    _haftalik_hedef_isle'de kullanılıyor; bu fonksiyon önceden sadece
    satirlari_ayikla'ya güveniyordu, bu da TEK satırlık 'ekle:' kalıbında
    (satır ':' ile BİTMEDİĞİ için) talimat cümlesinin tamamını görev metni
    sanan gerçek bir bug'dı - test sırasında yakalandı."""
    tirnak_ici = re.findall(r'["\u201c\u201d]([^"\u201c\u201d]+)["\u201c\u201d]', text)
    numarali_liste = satirlari_ayikla(text)

    if tirnak_ici:
        gorevler = tirnak_ici
    elif len(numarali_liste) > 1:
        gorevler = numarali_liste
    elif numarali_liste:
        tek = numarali_liste[0]
        if ":" in tek:
            olasi_talimat, icerik = tek.split(":", 1)
            talimat_kelimeleri = ["ekle", "kaydet", "yaz", "gir"]
            if icerik.strip() and any(k in olasi_talimat.lower() for k in talimat_kelimeleri):
                gorevler = [icerik.strip()]
            else:
                gorevler = [tek]
        else:
            gorevler = [tek]
    else:
        gorevler = []

    if not gorevler:
        send_message("Bunu görev listesi olarak anlayamadım, satır satır tekrar yazar mısın?")
        return
    ws = get_gorevler_sheet()
    bugun = bugun_str()

    # Eklemeden ÖNCE mevcut sayıyı al - "üzerine ekledim" gibi bağlam
    # farkında bir cevap verebilmek için (_haftalik_hedef_isle ile aynı
    # desen - önceden SADECE haftalık tarafta vardı, burada yoktu; bu
    # yüzden art arda gelen ekleme mesajları öncekileri hiç saymıyormuş
    # gibi görünen, ama Sheets'te aslında doğru biriken bir cevap veriyordu).
    mevcut_satirlar = ws.get_all_values()
    mevcut_sayisi = sum(1 for r in mevcut_satirlar[1:] if r and r[0] == bugun)

    for gorev in gorevler:
        guvenli_append_row(ws, [bugun, "", gorev, "Bekliyor"])
    set_bekleyen_soru("")

    toplam = mevcut_sayisi + len(gorevler)
    if mevcut_sayisi > 0:
        if len(gorevler) == 1:
            mesaj = (
                f"Mevcut {mevcut_sayisi} bugünkü görevinin üzerine "
                f"'{gorevler[0]}' görevini ekledim, toplam {toplam} oldu. Akşam soracağım!"
            )
        else:
            liste = "\n".join(f"{i+1}) {g}" for i, g in enumerate(gorevler))
            mesaj = (
                f"Mevcut {mevcut_sayisi} bugünkü görevinin üzerine {len(gorevler)} "
                f"yeni görev ekledim:\n{liste}\n\nToplam {toplam} oldu. Akşam soracağım!"
            )
    else:
        liste = "\n".join(f"{i+1}) {g}" for i, g in enumerate(gorevler))
        mesaj = f"Not aldım, bugünkü görevlerin:\n{liste}\n\nAkşam bunları soracağım!"

    send_message(mesaj)


def _hedef_kaydi_icin_hafta_baslangic_str():
    """Haftalık hedef KAYDI için doğru hafta başlangıcını hesaplar.
    `hafta_baslangic_str()` 'bugünü içeren haftanın' Pazartesi'sini
    döndürür - bu, SORGULAMA için doğru semantik (Pazar günü sorulan
    'bu hafta nasıl gidiyor' bugünü içeren haftaya, yani biten haftaya
    bakmalı). AMA hedef KAYDETME için farklı bir semantik gerekiyor:
    `pazar()` mesajı özellikle 'Yeni hafta başlıyor, gelecek haftanın
    hedefleri ne?' diye soruyor - kullanıcı Pazar günü (aynı gün içinde)
    cevap verdiğinde `hafta_baslangic_str()` hâlâ BİTMEKTE OLAN haftanın
    Pazartesi'sini (6 gün önce) döndürüyor, YARINKİ (yeni) haftanın
    Pazartesi'sini değil. Gerçek bir olayda bu, Pazar günü girilen
    hedeflerin yanlışlıkla bir önceki haftaya (20 Temmuz yerine 27
    Temmuz'a kaydedilmesi gerekirken) kaydedilmesine sebep oldu.
    Düzeltme: bugün Pazar ise (weekday()==6) YARINKİ Pazartesi'yi
    kullan; diğer tüm günlerde (hafta ortası ad-hoc ekleme, ör. 'haftalık
    hedeflerime şunu ekle') davranış DEĞİŞMİYOR - o zaten doğru şekilde
    cari/devam eden haftaya ekleniyor."""
    simdi = datetime.datetime.now(TR_TZ)
    if simdi.weekday() == 6:  # Pazar
        return (simdi + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    return hafta_baslangic_str()


def _haftalik_hedef_isle(text):
    """Hem 'bu haftanın hedefleri: ...' (tam liste, genelde Pazar) hem de
    'haftalık görevlerime şunu ekle: \"...\"' (haftanın ortasında tek/az
    sayıda ekleme) kalıplarını kapsar. Öncelik: (1) tırnak içi - en
    güvenilir, (2) numaralı/çok satırlı liste, (3) tek satırlık 'ekle:
    X' türü talimat cümlelerinde ':' sonrasını almak (talimatın kendisini
    hedef metni sanmamak için)."""
    tirnak_ici = re.findall(r'["\u201c\u201d]([^"\u201c\u201d]+)["\u201c\u201d]', text)
    numarali_liste = satirlari_ayikla(text)

    if tirnak_ici:
        hedefler = tirnak_ici
    elif len(numarali_liste) > 1:
        hedefler = numarali_liste
    elif numarali_liste:
        tek = numarali_liste[0]
        if ":" in tek:
            olasi_talimat, icerik = tek.split(":", 1)
            talimat_kelimeleri = ["ekle", "kaydet", "yaz", "gir"]
            if icerik.strip() and any(k in olasi_talimat.lower() for k in talimat_kelimeleri):
                hedefler = [icerik.strip()]
            else:
                hedefler = [tek]
        else:
            hedefler = [tek]
    else:
        hedefler = []

    if not hedefler:
        send_message("Bunu hedef listesi olarak anlayamadım, satır satır ya da tırnak içinde tekrar yazar mısın?")
        return

    ws = get_haftalik_sheet()
    hafta = _hedef_kaydi_icin_hafta_baslangic_str()

    # Eklemeden ÖNCE mevcut sayıyı al - "üzerine ekledim" gibi bağlam
    # farkında bir cevap verebilmek için.
    mevcut_satirlar = ws.get_all_values()
    mevcut_sayisi = sum(1 for r in mevcut_satirlar[1:] if r and r[0] == hafta)

    for hedef in hedefler:
        guvenli_append_row(ws, [hafta, hedef, "Bekliyor"])
    set_bekleyen_soru("")

    toplam = mevcut_sayisi + len(hedefler)
    if mevcut_sayisi > 0:
        if len(hedefler) == 1:
            mesaj = (
                f"Mevcut {mevcut_sayisi} haftalık hedefinin üzerine "
                f"'{hedefler[0]}' hedefini ekledim, toplam {toplam} oldu. 📝"
            )
        else:
            liste = "\n".join(f"{i+1}) {h}" for i, h in enumerate(hedefler))
            mesaj = (
                f"Mevcut {mevcut_sayisi} haftalık hedefinin üzerine {len(hedefler)} "
                f"yeni hedef ekledim:\n{liste}\n\nToplam {toplam} oldu. 📝"
            )
    else:
        liste = "\n".join(f"{i+1}) {h}" for i, h in enumerate(hedefler))
        mesaj = f"Haftalık hedeflerin kaydedildi:\n{liste}\n\nHafta ortasında kontrol edeceğim. 📝"

    send_message(mesaj)


def _sorgu_niyeti_var_mi(metin_kucuk):
    """Kullanıcı bir şey EKLEMİYOR, var olan bilgiyi SORUYOR/İSTİYOR.
    Bu True dönerse kural katmanı KESİNLİKLE bir tahminde bulunmamalı -
    tam olarak 'günlük görevlerimi sorgula lütfen' gibi mesajların kendi
    içeriğinde 'görevlerim' geçtiği için yanlışlıkla GUNLUK_GOREV
    sayılmasına yol açan asıl kör nokta buydu. NOT: bu fonksiyon bir
    kelime listesiyle çalıştığı için doğası gereği EKSİK olabilir (ör.
    'neler' sorusu ilk yazıldığında listede yoktu, gerçek bir olayda
    kaçırıldı) - bu yüzden asıl güvence bu listede değil, aşağıdaki
    _kural_tahmini'nin tek-maddeli mesajlarda salt bir İSİM (görevlerim/
    hedeflerim) yerine GERÇEK BİR EYLEM FİİLİ (ekle/kaydet) arayan yapısal
    tasarımında - bu liste sadece ek bir hızlı-yakalama katmanı."""
    sorgu_kaliplari = [
        "sorgula", "göster", "listele", "hatırlat", "nedir", "neydi",
        "neler", "ne kadar", "hangi", "gönderir misin", "gönder misin",
        "söyler misin", "yazar mısın", "durumum ne", "ilerledim mi",
        "kaçırdım", "ne kadar ilerledim", "kaç tane", "nerede", "kimin",
    ]
    if any(k in metin_kucuk for k in sorgu_kaliplari):
        return True
    # Soru kipi PARÇACIĞI (mı/mi/mu/mü ve türevleri) - Türkçe'de bu her
    # zaman AYRI bir kelimedir ('yaptın mı', 'geliyor musun'), bir isme
    # SUFFIX olarak eklenmez. Önceki hâlde baştaki '\w*' bu ayrımı
    # yapmıyordu - 'görevlerimi' gibi sıradan bir iyelik+belirtme eki
    # ('görevler' + 'im' + 'i') '...mi' ile bittiği için yanlışlıkla soru
    # kipi sanılıyordu (gerçek bir olayda "22 temmuz'dan kalan rutin ve
    # görevlerimi istiyorum" bu yüzden yanlış tetiklendi). Artık parçacık
    # SADECE bağımsız bir kelime olarak eşleşiyor.
    if re.search(r"\b(mı|mi|mu|mü|mısın|misin|musun|müsün|mıydı|miydi|mısınız|misiniz|musunuz|müsünüz)\b", metin_kucuk):
        return True
    return False


def _kural_tahmini(text):
    """ARTIK BİR ÖN-FİLTRE DEĞİL - SLM'in kararını DOĞRULAYAN bağımsız,
    ikinci bir görüş. Sadece çok net kalıplarda (liste/madde + açık
    'kaydet/ekle' niyeti + SORGU SİNYALİ YOK -> GUNLUK_GOREV/HAFTALIK_HEDEF;
    ya da geçmiş bir tarih referansı + kaydet niyeti YOK -> SORGULA)
    kendinden emin bir tahmin üretir; aksi halde None döner ('kararsızım,
    SLM'e güveniyorum' anlamına gelir - None dönmesi ASLA bir anlaşmazlık
    sayılmaz). _siniflandir_ve_isle bu fonksiyonu SLM'den SONRA çağırıp
    sonucu karşılaştırır; sadece ikisi ÇELİŞİRSE daha güçlü modele (7b)
    eskalasyon yapılır."""
    metin_kucuk = text.lower()

    if _sorgu_niyeti_var_mi(metin_kucuk):
        return None

    kaydet_niyeti_var = any(k in metin_kucuk for k in [
        "kaydet", "kayıt et", "ekle", "ekliyorum", "yazıyorum",
    ])

    # Geçmiş görev tamamlama güvenlik ağı: mesajda tırnak içi bir görev VE
    # geçmiş zamanlı bir tamamlama fiili (yaptım/yapmıştım/tamamladım/
    # bitirdim/bitirmiştim) varsa VE açık bir 'ekle/kaydet' niyeti YOKSA,
    # bu neredeyse kesin bir GECMIS_GOREV_TAMAMLA'dır - kimse tırnak içinde
    # bir görevi GEÇMİŞ ZAMANLA anıp aynı anda onu YENİ ekliyor olamaz.
    # Bu kontrol tarih güvenlik ağından ÖNCE geliyor çünkü '22 Temmuz'daki
    # X görevini yapmıştım' gibi bir mesaj her ikisini de tetikleyebilir -
    # tamamlama niyeti burada daha spesifik/doğru sinyal. Gerçek bir olayda
    # SLM(3b) bunu GUNLUK_GOREV sanıp bugüne sahte bir görev daha ekledi,
    # bu kural o durumu 7b'ye eskale eder.
    tirnak_var = '"' in text or "\u201c" in text or "\u201d" in text
    tamamlama_fiili_var = any(k in metin_kucuk for k in [
        "yaptım", "yapmıştım", "tamamladım", "bitirdim", "bitirmiştim",
    ])
    if tirnak_var and tamamlama_fiili_var and not kaydet_niyeti_var:
        return "GECMIS_GOREV_TAMAMLA"

    # Geçmiş tarih güvenlik ağı: mesajda 'dün' ya da '22 Temmuz' gibi somut
    # bir GEÇMİŞ tarih referansı varsa VE açık bir kaydet/ekle niyeti YOKSA,
    # bu neredeyse kesin bir SORGULA'dır - kimse geçmiş bir tarihi anıp yeni
    # bir görev/hedef eklemez, geçmişe dair bilgi ister. Bu kural, SLM'in
    # geçmiş tarihli sorguları (tanımında örnek verilmemiş olabilir diye)
    # yanlışlıkla SOHBET sanmasına karşı bir ikinci güvenlik katmanı -
    # gerçek bir olayda ("22 temmuz'dan kalan görevlerimi istiyorum") 3b
    # bunu SOHBET sanmıştı, bu kural o durumu 7b'ye eskale eder.
    if not kaydet_niyeti_var and metinden_tarih_cikar(text) is not None:
        return "SORGULA"

    maddeler = satirlari_ayikla(text)
    if not maddeler:
        return None

    gunluk_sinyali = "günlük" in metin_kucuk or "bugün" in metin_kucuk
    haftalik_sinyali = "hafta" in metin_kucuk

    if len(maddeler) > 1:
        # Çok maddeli (numaralı/çok satırlı) bir liste, kendi başına
        # neredeyse kesin bir "içerik sağlama" (dictation) sinyalidir -
        # kimse birden çok maddeyi sıralayıp sonra soru sormaz. Burada bir
        # 'ekle/kaydet' fiili aramaya GEREK YOK, tam da bu yüzden numaralı
        # liste akışları (ör. 'bugünkü görevlerim: 1) ... 2) ...') zaten
        # hiç 'ekle' fiili içermeden çalışıyordu ve çalışmaya devam etmeli.
        if haftalik_sinyali and not gunluk_sinyali:
            return "HAFTALIK_HEDEF"
        if gunluk_sinyali:
            return "GUNLUK_GOREV"
        return None

    # TEK maddelik mesajlarda durum FARKLI ve daha riskli: 'görevlerim/
    # hedeflerim/yapacaklarım' gibi bir İSMİN varlığı TEK BAŞINA yeterli
    # bir sinyal DEĞİL - hem 'bugünkü görevim: toplantıya git' (ekleme)
    # HEM 'kalan günlük görevlerim neler' (sorgu) bu ismi içerebilir; isim
    # sadece KONUYU belirtir, NİYETİ değil. Gerçek bir olayda bu ayrım
    # yokken "kalan günlük görevlerim neler" yanlışlıkla GUNLUK_GOREV
    # sayılıp gerçek bir görev gibi kaydedildi. Artık tek maddelik
    # mesajlarda SADECE gerçek bir eylem fiili (ekle/kaydet/yaz/gir) kabul
    # ediliyor - bare bir isim asla yeterli değil.
    eylem_fiili_var = any(k in metin_kucuk for k in [
        "kaydet", "kayıt et", "yazıyorum", "ekliyorum", "ekleme yap", "ekle",
    ])
    if not eylem_fiili_var:
        return None

    if len(maddeler) == 1 and not gunluk_sinyali and not haftalik_sinyali:
        return None

    if haftalik_sinyali and not gunluk_sinyali:
        return "HAFTALIK_HEDEF"
    return "GUNLUK_GOREV"


SOSYAL_MEDYA_LIMIT_DAKIKA = 90  # Kullanıcının kendi belirlediği günlük boşa vakit sınırı

# Alternatif, daha faydalı aktivite kategorileri ve bunları GunlukGorevler
# metninde tespit etmeye yarayan anahtar kelimeler. 'Verimli video izleme'
# rutini ayrıca kontrol ediliyor (bkz. _bugun_yapilan_alternatif_aktiviteler).
_ALTERNATIF_AKTIVITE_ANAHTAR_KELIMELER = {
    "kitap okuma": ["kitap"],
    "müzik yapma/dinleme": ["müzik", "gitar", "piyano"],
    "hava alma/yürüyüş": ["hava al", "yürüyüş", "yürü"],
}


def _sureyi_dakikaya_cevir(text):
    """SLM'in SURE_DAKIKA alanı boş/geçersiz gelirse devreye giren basit
    regex tabanlı bir güvenlik ağı - 'X saat', 'Y dakika', 'yarım saat',
    'bir buçuk saat' gibi yaygın kalıpları yakalar. Süre çıkaramazsa None
    döner (kesin bilmediğimiz bir sayıyı ASLA uydurmayız)."""
    metin = text.lower()
    toplam = 0.0
    bulundu = False

    if re.search(r"bir\s*buçuk\s*saat|1[.,]5\s*saat", metin):
        toplam += 90
        bulundu = True
    elif "yarım saat" in metin:
        toplam += 30
        bulundu = True
    else:
        saat_match = re.search(r"(\d+(?:[.,]\d+)?)\s*saat", metin)
        if saat_match:
            toplam += float(saat_match.group(1).replace(",", ".")) * 60
            bulundu = True

    dakika_match = re.search(r"(\d+)\s*dak", metin)
    if dakika_match:
        toplam += int(dakika_match.group(1))
        bulundu = True

    return int(round(toplam)) if bulundu else None


def _gun_tamamlanma_durumu(tarih):
    """Belirtilen tarih için TÜM ad-hoc günlük görevlerin ve TÜM aktif
    rutinlerin tamamlanıp tamamlanmadığını kontrol eder. Döner:
    (hepsi_tamam: bool, eksikler: [str] - hem görev hem rutin adları,
    karışık, ilk bulunanlar önce)."""
    eksikler = []

    ws_gorev = get_gorevler_sheet()
    for r in ws_gorev.get_all_records():
        if r.get("Tarih") == tarih and r.get("Durum") != "Yapıldı":
            eksikler.append(r["GorevMetni"])

    cevaplanan = cevaplanan_rutinler(tarih)
    ws_takip = get_sheet()
    rutin_durumlari = {
        r["Görev"]: r["Durum"] for r in ws_takip.get_all_records()
        if r.get("Tarih") == tarih
    }
    for rutin in get_aktif_rutinler():
        durum = rutin_durumlari.get(rutin["isim"])
        if rutin["isim"] not in cevaplanan or durum not in ("Yapıldı", "Telafi"):
            eksikler.append(rutin["isim"])

    return (len(eksikler) == 0), eksikler


def _bugun_yapilan_alternatif_aktiviteler(tarih):
    """O gün zaten 'Yapıldı' olarak işaretlenmiş alternatif aktiviteleri
    (kitap/müzik/hava alma/faydalı video) tespit eder - böylece öneri
    listesi, kullanıcının o gün ZATEN yaptığı bir şeyi tekrar önermez
    (ör. 'kitap okuyabilirdin' demek, o gün zaten kitap okuduysa saçma olur)."""
    yapilanlar = set()

    ws_takip = get_sheet()
    for r in ws_takip.get_all_records():
        if (r.get("Tarih") == tarih and r.get("Görev") == "Verimli video izleme"
                and r.get("Durum") in ("Yapıldı", "Telafi")):
            yapilanlar.add("belgesel/faydalı video izleme")

    ws_gorev = get_gorevler_sheet()
    for r in ws_gorev.get_all_records():
        if r.get("Tarih") != tarih or r.get("Durum") != "Yapıldı":
            continue
        metin_kucuk = r.get("GorevMetni", "").lower()
        for kategori, kelimeler in _ALTERNATIF_AKTIVITE_ANAHTAR_KELIMELER.items():
            if any(k in metin_kucuk for k in kelimeler):
                yapilanlar.add(kategori)

    return yapilanlar


def _bosa_vakit_cevabini_olustur(dakika, tarih, faydali_dakika=None, belirsiz_faydali_var=False):
    """Boşa vakit cevabını, o günün GERÇEK görev/rutin tamamlanma
    durumuna bakarak bağlam-farkında şekilde oluşturur:
    - Sınırın altındaysa: tebrik.
    - Sınırı aştıysa VE bir şey eksikse: eksik olanı adıyla anıp daha
      net/sert ama destekleyici bir ton.
    - Sınırı aştıysa AMA her şey tamamsa: nazik bir öneri - SADECE o gün
      zaten yapılmamış alternatif aktiviteleri önerir, hiçbiri kalmadıysa
      öneri cümlesini hiç eklemez.

    faydali_dakika: kullanıcı sürenin bir kısmının faydalı içerik olduğunu
    SAYISAL olarak belirttiyse (ör. '60 dk Instagram ama 20 dk'sı faydalı
    bir videoydu'), bu kısım toplam süreden düşülüp GERÇEK boşa vakit
    üzerinden değerlendirme yapılır - kullanıcının "SLM'e bağlamamışız"
    diye işaret ettiği eksiklik buydu.
    belirsiz_faydali_var: kullanıcı sayı vermeden "bir kısmı faydalıydı"
    gibi belirsiz bir ifade kullandıysa True - bu durumda düşülecek net
    bir sayı yok, ama kullanıcıya daha net yazarsa daha isabetli
    değerlendirebileceğimizi nazikçe hatırlatıyoruz."""
    ifade = _gun_ifadesi(tarih)

    if dakika is None:
        return (
            f"Not aldım - ama net bir süre anlayamadım. Dakika ya da saat "
            f"cinsinden söylersen ({SOSYAL_MEDYA_LIMIT_DAKIKA} dk'lık "
            f"sınırınla karşılaştırıp) gerçek bir değerlendirme yapabilirim. 📝"
        )

    belirsiz_not = (
        " (Bir kısmının faydalı olduğunu belirttin ama net bir dakika "
        "vermediğin için tamamını saydım - 'X dakikası faydalıydı' "
        "dersen daha isabetli değerlendiririm.)"
        if belirsiz_faydali_var and faydali_dakika is None else ""
    )

    if faydali_dakika is not None and faydali_dakika > 0:
        gercek_bosa = max(0, dakika - faydali_dakika)
        on_not = (
            f"Toplam {dakika} dakikadan {faydali_dakika} dakikasını faydalı "
            f"içerik olarak ayırdım, gerçek boşa vakit {gercek_bosa} dakika. "
        )
        dakika = gercek_bosa
    else:
        on_not = ""

    if dakika <= SOSYAL_MEDYA_LIMIT_DAKIKA:
        return (
            f"{on_not}Harika, {dakika} dakika ile {SOSYAL_MEDYA_LIMIT_DAKIKA} "
            f"dakikalık sınırının altında kaldın. Tebrikler {KULLANICI_ADI}! 🎉{belirsiz_not}"
        )

    asilan = dakika - SOSYAL_MEDYA_LIMIT_DAKIKA
    hepsi_tamam, eksikler = _gun_tamamlanma_durumu(tarih)

    if not hepsi_tamam:
        ilk_eksik = eksikler[0]
        return (
            f"{on_not}'{ilk_eksik}' henüz tamamlanmamışken sosyal medyada {dakika} "
            f"dakika ({SOSYAL_MEDYA_LIMIT_DAKIKA} dk sınırını {asilan} dk "
            f"aşarak) geçirmen düşündürücü {KULLANICI_ADI}. Bunu kendine karşı "
            "bir uyarı olarak gör - planına dönmek için hâlâ vaktin var, "
            f"kendine karşı sabırlı ama net ol. 💪{belirsiz_not}"
        )

    yapilmis = _bugun_yapilan_alternatif_aktiviteler(tarih)
    onerilebilecekler = [
        a for a in ["belgesel/faydalı video izleme", "kitap okuma", "müzik yapma/dinleme", "hava alma/yürüyüş"]
        if a not in yapilmis
    ]

    mesaj = (
        f"{on_not}Bugünkü tüm görev ve rutinlerini tamamlamışsın, bu iyi haber - "
        f"ama {dakika} dakika ile sınırını {asilan} dk aştın."
    )
    if onerilebilecekler:
        oneri = " ya da ".join(onerilebilecekler[:2])
        mesaj += f" O fazladan zamanı {oneri} gibi bir şeye ayırabilirdin."
    return mesaj + " 💭" + belirsiz_not


def _siniflandir_ve_isle(text, bekleyen):
    """Gelen her serbest metni SLM'e sınıflandırtır. 'bekleyen' sadece bir
    BAĞLAM/ipucu olarak veriliyor - kesin kural değil. Model, mesajın
    içeriğine bakıp en uygun kategoriyi kendisi seçiyor. Bu, katı bir
    durum makinesinin (sabit 'şu an şunu bekliyorum -> öyle işle' mantığının)
    beklenmedik senaryolarda yanlış kategoriye yazması sorununu çözer.

    MİMARİ (güncel): Artık deterministik kural katmanı bir ÖN-FİLTRE değil,
    SLM'in kararını sonradan DOĞRULAYAN bağımsız bir ikinci görüş. Önceden
    kurallar SLM'e sormadan ÖNCE devreye girip mesajı kesebiliyordu - bu,
    SLM'in bildiği bağlamdan (bekleyen soru, soru kipi tespiti vb.)
    tamamen habersiz bir kaba anahtar-kelime eşleşmesinin, SLM zaten doğru
    bilecek durumları (ör. sorgu cümleleri) ele geçirmesine yol açıyordu.
    Şimdi SLM HER ZAMAN önce çalışır; kural katmanı sadece SLM'in kararıyla
    ÇELİŞTİĞİ (ve kuralın kendinden gerçekten emin olduğu) nadir durumlarda
    devreye girip daha güçlü modele (7b) ikinci bir görüş sorar."""

    baglam = (
        f"Kullanıcıya az önce sorduğum, henüz cevap bekleyen bir soru var: "
        f"{BEKLEYEN_ACIKLAMA.get(bekleyen, bekleyen)}."
        if bekleyen else
        "Şu an kullanıcıya sorduğum, cevap beklediğim bir soru yok."
    )

    aktif_rutinler = get_aktif_rutinler()
    rutin_isim_listesi = ", ".join(f"'{r['isim']}'" for r in aktif_rutinler)
    aktif_haftalik_rutinler = get_aktif_haftalik_rutinler()
    haftalik_rutin_isim_listesi = ", ".join(f"'{r['isim']}'" for r in aktif_haftalik_rutinler)

    prompt = (
        "Sen bir verimlilik takip botusun (adın Poke). "
        f"{baglam}\n\n"
        f"Kullanıcı şunu yazdı:\n\"{text}\"\n\n"
        "Bu mesajı aşağıdaki kategorilerden EN UYGUN olanına ata "
        "(bekleyen soru sadece bir ipucu, mesajın gerçek içeriğine göre "
        "karar ver - biri başka bir konuda yazmış olabilir):\n"
        "- GUNLUK_GOREV: bugün için yapılacaklar listesi veriyor (kullanıcı "
        "kendi içeriğini/madde listesini SAĞLIYOR, YENİ görev(ler) olarak "
        "eklenmesini istiyor). ÇOK ÖNEMLİ KURAL: "
        "'bugün/bugünkü/günlük' kelimelerinden HERHANGİ biri geçiyorsa VE "
        "'hafta/haftalık' kelimesi HİÇ GEÇMİYORSA, bu KESİNLİKLE "
        "GUNLUK_GOREV'dir, HAFTALIK_HEDEF ASLA DEĞİLDİR - liste veriyor "
        "olması (madde madde yazması) seni HAFTALIK_HEDEF sanmaya İTMESİN. "
        "AMA BU KURAL SORGULA KURALINDAN SONRA GELİR: mesaj soru kipindeyse "
        "(mı/mi/mu/mü İLE YA DA 'ne/neler/nedir/kaç/hangi/nereye' gibi soru "
        "sözcükleriyle) VE kullanıcı kendi içeriğini SAĞLAMIYORSA (sadece "
        "soruyor), 'günlük' kelimesi geçse bile bu SORGULA'dır, "
        "GUNLUK_GOREV DEĞİLDİR - ör. 'kalan günlük görevlerim neler' bir "
        "SORGULA'dır, içinde 'günlük' geçmesi onu GUNLUK_GOREV yapmaz. "
        "HAFTALIK_HEDEF SADECE 'hafta/haftalık' kelimesi AÇIKÇA geçtiğinde "
        "kullanılır, başka hiçbir durumda değil. AYRICA ÇOK ÖNEMLİ: eğer "
        "kullanıcı tırnak içinde bir görev anıp GEÇMİŞ ZAMANLA "
        "('yaptım'/'yapmıştım'/'tamamladım'/'bitirdim' gibi) TAMAMLADIĞINI "
        "söylüyorsa, bu GUNLUK_GOREV DEĞİL, GECMIS_GOREV_TAMAMLA'dır - "
        "'günlük' kelimesi geçse bile, YENİ bir görev SAĞLAMIYOR, VAR OLAN "
        "bir görevi tamamladığını bildiriyor\n"
        "- HAFTALIK_HEDEF: bu haftanın hedeflerini veriyor VEYA mevcut "
        "haftalık hedeflere yeni ekleme yapıyor (ör. 'haftalık hedeflere "
        "ekle: piyano çal' - 'hafta/haftalık' kelimesi + ekleme niyeti "
        "varsa bu kategori, YENI_GOREV DEĞİL)\n"
        "- BOSA_VAKIT: bugün ne kadar boşa vakit geçirdiğini anlatıyor\n"
        "- YENI_GOREV: herhangi bir an kendiliğinden YENİ bir GÜNLÜK "
        "(haftalık DEĞİL) görev/iş EKLİYOR (şimdiki/gelecek zaman: "
        "'ekliyorum', 'ekle', henüz yapılmamış bir şey). 'hafta/haftalık' "
        "kelimesi GEÇMİYORSA bu kategori kullanılır. Kullanıcı genelde "
        "eklenecek görev(ler)i tırnak içinde yazar, "
        "ör: 'bugüne şunu ekliyorum: \"kitap oku\", \"spor yap\"' - birden "
        "fazla görev aynı mesajda olabilir.\n"
        "- GECMIS_GOREV_TAMAMLA: kullanıcı GEÇMİŞTE (bugün ya da önceki "
        "bir günde) kendi eklediği bir GÜNLÜK GÖREVİ (sabit rutin "
        "listesinde OLMAYAN, kullanıcının kendi yazdığı ad-hoc bir iş) "
        "aslında TAMAMLADIĞINI bildiriyor, kaydı düzeltmek istiyor. "
        "ÇOK DİKKAT: YENI_GOREV ile TAM AYNI yüzeysel özelliği (tırnak "
        "içinde görev adı) paylaşır - bu ikisini birbirinden ayıran TEK "
        "ŞEY FİİLİN ZAMANIDIR, başka hiçbir ipucuna güvenme. Doğrudan "
        "karşılaştır (aynı görev metniyle, sadece fiil zamanı farklı):\n"
        "    * '\"kitap oku\" ekliyorum' -> YENI_GOREV (şimdiki zaman, "
        "henüz yapılmadı, YENİ bir şey ekleniyor)\n"
        "    * '\"kitap oku\" yaptım' / '\"kitap oku\" yapmıştım' -> "
        "GECMIS_GOREV_TAMAMLA (geçmiş zaman, ZATEN tamamlanmış, sadece "
        "kayıt düzeltiliyor, hiçbir şey YENİ eklenmiyor)\n"
        "Kısacası: 'yaptım'/'yapmıştım'/'tamamladım'/'bitirdim'/"
        "'bitirmiştim' gibi GEÇMİŞ ZAMANLI bir fiil + tırnak içinde bir "
        "görev adı görürsen, tırnağın kendisine ALDANMA - bu KESİNLİKLE "
        "GECMIS_GOREV_TAMAMLA'dır, YENI_GOREV/GUNLUK_GOREV ASLA DEĞİLDİR. "
        "Kullanıcı bazen tarih de ekler (ör. '\"kitap oku (2026-07-20)\" "
        "yapmıştım' - bu da GECMIS_GOREV_TAMAMLA'dır)\n"
        f"- RUTIN_TAMAMLA: kullanıcı şu sabit GÜNLÜK rutinlerden birini "
        f"tamamladığını bildiriyor: {rutin_isim_listesi}. VEYA şu HAFTALIK "
        f"(tekrarlayan, hangi gün önemli değil) rutinlerden birini: "
        f"{haftalik_rutin_isim_listesi or '(tanımlı yok)'}. Ör: 'Fransızca "
        "rutinimi tamamladım', 'bugün spor yaptım', 'oda tozunu aldım' gibi "
        "doğal cümleler. YENI_GOREV ile KARIŞTIRMA - bu kategori sadece "
        "yukarıdaki listelerdeki rutinler için\n"
        "- SORGULA: kullanıcı bir şeyi EKLEMİYOR, var olan bilgiyi SORUYOR/"
        "İSTİYOR/HATIRLATMAMI istiyor. Ör: 'bugünkü görevlerimi hatırlatır "
        "mısın', 'bu hafta hedeflerim neydi', 'hangi rutinleri kaçırdım', "
        "'bugünkü rutin tamamlama listemi gönderir misin', 'durumum ne', "
        "'ne kadar ilerledim', 'kalan günlük görevlerim neler'. ÖNEMLİ KURAL: "
        "eğer cümle soru kipiyle bitiyorsa (mı/mi/mu/mü/misin/mısın/mısınız "
        "vb. İLE YA DA 'ne/neler/nedir/kaç/hangi/nereye/kim' gibi soru "
        "sözcükleriyle) VE kullanıcı kendisi bir liste/içerik SAĞLAMIYORSA "
        "(sadece istek/talep var), bu KESİNLİKLE SORGULA'dır, ASLA "
        "GUNLUK_GOREV/HAFTALIK_HEDEF/YENI_GOREV değildir - o kategoriler "
        "SADECE kullanıcı kendi içeriğini (görev/hedef metni) verdiğinde "
        "kullanılır. AYRICA ÖNEMLİ: kullanıcı GEÇMİŞ bir tarihe ait görev/rutin "
        "bilgisini istiyorsa (ör. 'dün ne yapmıştım', '22 Temmuz'dan kalan "
        "görevlerimi istiyorum', 'geçen hafta salı ne yapacaktım') bu DA "
        "SORGULA'dır, SOHBET DEĞİLDİR - tarihin bugün olmaması onu SOHBET "
        "yapmaz, sadece geçmişe dönük bir SORGULA örneğidir\n"
        "- SOHBET: yukarıdakilerin hiçbiriyle ilgili değil, genel sohbet/soru\n\n"
        "SADECE şu formatta cevap ver, başka hiçbir şey ekleme:\n"
        "TIP: <KATEGORI>\n"
        "GOREVLER: <SADECE TIP=YENI_GOREV ise: her görevi \" | \" ile "
        "ayırarak yaz (tırnak işaretleri olmadan). Diğer TIP'lerde boş bırak>\n"
        f"RUTIN: <SADECE TIP=RUTIN_TAMAMLA ise: şu listelerden BİREBİR aynı "
        f"şekilde yaz, birden fazla rutin tamamlandıysa \" | \" ile ayır: "
        f"{rutin_isim_listesi}, {haftalik_rutin_isim_listesi}. Diğer TIP'lerde boş bırak>\n"
        "SURE_DAKIKA: <SADECE TIP=BOSA_VAKIT ise: kullanıcının anlattığı "
        "TOPLAM süreyi DAKİKA cinsinden tam sayı olarak yaz (ör. '1 saat 30 "
        "dakika' -> 90, 'yaklaşık 40 dakika' -> 40, '2 saat' -> 120, '60 "
        "dakika Instagram 30 dakika YouTube' -> 90 - hepsini TOPLA). Net "
        "bir süre çıkaramıyorsan boş bırak. Diğer TIP'lerde boş bırak>\n"
        "FAYDALI_DAKIKA: <SADECE TIP=BOSA_VAKIT ise VE kullanıcı bu sürenin "
        "bir kısmının FAYDALI/ÜRETKEN içerik olduğunu SAYISAL olarak "
        "belirtmişse (ör. '30 dakikası faydalı bir video izlemekti', "
        "'20 dakika belgesel de vardı') o sayıyı yaz. Kullanıcı sadece "
        "belirsiz bir ifade kullanmışsa ('bir kısmı faydalıydı', 'kısmen "
        "faydalıydı' gibi - SAYI VERMEMİŞSE) BOŞ BIRAK, sayı uydurma. "
        "Diğer TIP'lerde boş bırak>\n"
        "CEVAP: <kullanıcıya vereceğin kısa (1-2 cümle), doğal, samimi Türkçe "
        "yanıt - SADECE Türkçe ve Latin alfabesi kullan, başka dil/alfabe YASAK. "
        "TIP=BOSA_VAKIT ise bu alanı boş bırakabilirsin - asıl cevap ayrıca "
        "Python tarafında, o günün gerçek görev/rutin durumuna bakılarak "
        "oluşturuluyor. "
        "ÇOK ÖNEMLİ KURAL: TIP=SOHBET ya da SORGULA ise, ASLA 'kaydettim', "
        "'ekledim', 'belirledim', 'işledim' gibi bir EYLEMİ YAPMIŞ GİBİ KONUŞMA "
        "- bu kategorilerde HİÇBİR ŞEY KAYDEDİLMEZ, sadece konuşma/soru cevabı "
        "verilir. Yapılmamış bir şeyi yapmış gibi söylemek YASAK."
    )

    def _sonucu_parcala(sonuc_metni):
        tip_match = re.search(r"TIP:\s*(\w+)", sonuc_metni)
        gorevler_match = re.search(r"GOREVLER:\s*(.+)", sonuc_metni)
        rutin_match = re.search(r"RUTIN:\s*(.+)", sonuc_metni)
        sure_dakika_match = re.search(r"SURE_DAKIKA:\s*(\d+)", sonuc_metni)
        faydali_dakika_match = re.search(r"FAYDALI_DAKIKA:\s*(\d+)", sonuc_metni)
        cevap_match = re.search(r"CEVAP:\s*(.+)", sonuc_metni, re.DOTALL)
        tip_ = tip_match.group(1).upper() if tip_match else "SOHBET"
        cevap_ = cevap_match.group(1).strip() if cevap_match else "Not aldım 👍"
        sure_dakika_ = int(sure_dakika_match.group(1)) if sure_dakika_match else None
        faydali_dakika_ = int(faydali_dakika_match.group(1)) if faydali_dakika_match else None
        if _turkce_disi_karakter_var_mi(cevap_):
            cevap_ = "Not aldım 👍"
        return tip_, gorevler_match, rutin_match, cevap_, sure_dakika_, faydali_dakika_

    try:
        sonuc = slm_sorgula(prompt)
    except Exception as e:
        print(f"SLM hatası (sınıflandırma): {e}")
        send_message("Şu an bunu işleyemedim (teknik bir sorun oldu) — tekrar dener misin?")
        return

    tip, gorevler_match, rutin_match, cevap, sure_dakika, faydali_dakika = _sonucu_parcala(sonuc)

    # DOĞRULAMA: kural katmanı SLM'in kararına katılıyor mu? Kural sadece
    # gerçekten emin olduğu durumlarda bir görüş bildirir (None dönerse
    # bu ASLA anlaşmazlık sayılmaz - SLM'in kararı olduğu gibi kullanılır).
    kural_tahmini = _kural_tahmini(text)

    if kural_tahmini == "GECMIS_GOREV_TAMAMLA" and tip != "GECMIS_GOREV_TAMAMLA":
        # ÖZEL DURUM: gerçek bir olayda bu kalıpta (tırnak içi + geçmiş
        # zamanlı tamamlama fiili) hem 3b HEM 7b'nin AYNI yanlış kategoriye
        # (GUNLUK_GOREV) düştüğü görüldü - eskalasyon burada işe yaramıyor,
        # çünkü iki katman da aynı hataya düşebiliyor. Kural burada
        # dilbilimsel olarak çok güvenilir (tırnak içinde geçmiş zamanla
        # anılan bir metin neredeyse hiçbir zaman 'yeni ekle' anlamına
        # gelmez) VE alt işleyici (_gecmis_gorev_tamamla_isle) kendi
        # güvenlik ağına sahip (eşleşme bulunamazsa ASLA tahmin etmez,
        # netleştirme ister) - bu yüzden SLM'e danışmadan doğrudan kurala
        # güveniliyor. Bonus: gereksiz bir 7b çağrısından (ve onun Ollama
        # segfault riskinden) da kaçınılmış oluyor.
        print(f"[sınıflandırma] GECMIS_GOREV_TAMAMLA: SLM(3b)={tip} yanlış, kural doğrudan kullanılıyor (bilinen kör nokta)")
        log_anlasmazlik(text, kural_tahmini, tip, "KURAL DOĞRUDAN KULLANILDI (bilinen SLM kör noktası)")
        tip = "GECMIS_GOREV_TAMAMLA"
    elif kural_tahmini is not None and kural_tahmini != tip:
        print(f"[sınıflandırma] Anlaşmazlık: kural={kural_tahmini} slm(3b)={tip} - 7b'ye eskale ediliyor")
        try:
            sonuc_7b = slm_sorgula(prompt, model=SLM_MODEL_KALITELI)
            tip_7b, gorevler_match_7b, rutin_match_7b, cevap_7b, sure_dakika_7b, faydali_dakika_7b = _sonucu_parcala(sonuc_7b)
            log_anlasmazlik(text, kural_tahmini, tip, tip_7b)
            tip, gorevler_match, rutin_match, cevap, sure_dakika, faydali_dakika, sonuc = (
                tip_7b, gorevler_match_7b, rutin_match_7b, cevap_7b, sure_dakika_7b, faydali_dakika_7b, sonuc_7b
            )
        except Exception as e:
            print(f"7b eskalasyonu başarısız oldu, 3b kararında kalınıyor: {e}")
            log_anlasmazlik(text, kural_tahmini, tip, f"ESKALASYON BAŞARISIZ: {e}")

    log_slm_karari(tip, text, prompt, sonuc)

    if tip == "RUTIN_TAMAMLA":
        rutin_ham_liste = rutin_match.group(1).strip() if rutin_match else ""
        adaylar = [r.strip().strip("'\"") for r in rutin_ham_liste.split("|") if r.strip()]
        gunluk_isimler = {r["isim"] for r in aktif_rutinler}
        haftalik_isimler = {r["isim"]: r["id"] for r in aktif_haftalik_rutinler}

        gunluk_eslesen = [ad for ad in adaylar if ad in gunluk_isimler]
        haftalik_eslesen = [ad for ad in adaylar if ad in haftalik_isimler]

        if gunluk_eslesen or haftalik_eslesen:
            tarih = metinden_tarih_cikar(text)
            for isim in gunluk_eslesen:
                log_to_sheet(isim, "Yapıldı", tarih=tarih)

            if haftalik_eslesen:
                ws_takip = get_haftalik_rutin_takip_sheet()
                rows = ws_takip.get_all_values()
                hafta = hafta_baslangic_str()
                for isim in haftalik_eslesen:
                    rutin_id = haftalik_isimler[isim]
                    bulundu = False
                    for i, row in enumerate(rows[1:], start=2):
                        if row[0] == hafta and row[1] == rutin_id:
                            ws_takip.update_cell(i, 4, "Yapıldı")
                            bulundu = True
                            break
                    if not bulundu:
                        guvenli_append_row(ws_takip, [hafta, rutin_id, isim, "Yapıldı"])

            liste = ", ".join(f"'{i}'" for i in gunluk_eslesen + haftalik_eslesen)
            send_message(f"✅ {liste} tamamlandı olarak kaydedildi. Tebrikler!")
        else:
            send_message(
                "Hangi rutinden bahsettiğini tam anlayamadım — akşam kontrolünde "
                "butonla işaretleyebilirsin, orası her zaman güvenilir çalışır 👍"
            )

    elif tip == "GECMIS_GOREV_TAMAMLA":
        _gecmis_gorev_tamamla_isle(text)

    elif tip == "GUNLUK_GOREV":
        _gunluk_gorev_isle(text)

    elif tip == "HAFTALIK_HEDEF":
        _haftalik_hedef_isle(text)

    elif tip == "BOSA_VAKIT":
        tarih = metinden_tarih_cikar(text) or bugun_str()
        log_to_sheet("Boşa geçen vakit", "Beyan", text, tarih=tarih)
        set_bekleyen_soru("")
        metin_kucuk = text.lower()

        # ÖNEMLİ GÜVENLİK DÜZELTMESİ: gerçek bir olayda kullanıcı sadece
        # "1 saat 50 dakika sosyal medyada boşa vakit geçirmişim" dedi
        # (hiçbir faydalı kısım belirtmeden), ama SLM "SURE_DAKIKA: 130,
        # FAYDALI_DAKIKA: 40" gibi metinde HİÇ GEÇMEYEN sayılar UYDURDU.
        # Artık regex tabanlı çıkarım (_sureyi_dakikaya_cevir) HER ZAMAN
        # önceliklidir - o, sadece metinde GERÇEKTEN yazan sayıları bulur,
        # halüsinasyon yapamaz. SLM'in SURE_DAKIKA'sı SADECE regex hiçbir
        # şey bulamazsa (ör. çok yaratıcı/dolaylı bir ifade) yedek olarak
        # kullanılır.
        dakika_regex = _sureyi_dakikaya_cevir(text)
        dakika = dakika_regex if dakika_regex is not None else sure_dakika

        # FAYDALI_DAKIKA için DAHA DA SIKI bir güvenlik ağı: metinde
        # 'faydalı/yararlı/verimli' gibi bir kelime GEÇMİYORSA, SLM ne
        # derse desin bu alanı TAMAMEN yok sayıyoruz - kullanıcı hiç
        # böyle bir ayrım yapmadıysa, SLM'in uydurduğu bir sayıya asla
        # güvenilmemeli. Kelime geçse bile, faydalı kısım toplamdan
        # büyükse (mantıksız) yine reddediliyor.
        faydali_kelime_var = any(k in metin_kucuk for k in ["faydalı", "yararlı", "verimli"])
        faydali_dakika_guvenli = faydali_dakika if faydali_kelime_var else None
        if (faydali_dakika_guvenli is not None and dakika is not None
                and faydali_dakika_guvenli >= dakika):
            faydali_dakika_guvenli = None

        belirsiz_faydali_var = any(
            k in metin_kucuk for k in ["bir kısmı", "kısmen", "biraz faydalı", "bir kısmında"]
        )
        send_message(_bosa_vakit_cevabini_olustur(
            dakika, tarih, faydali_dakika=faydali_dakika_guvenli, belirsiz_faydali_var=belirsiz_faydali_var
        ))

    elif tip == "SORGULA":
        _sorguyu_cevapla(text)

    elif tip == "YENI_GOREV":
        # Öncelik sırası: (1) tırnak içi - en güvenilir, (2) numaralı satır
        # yapısı varsa satirlari_ayikla - deterministik ve başlık/giriş
        # cümlelerini zaten eliyor, (3) modelin kendi GOREVLER listesi -
        # model bazen başlık cümlesini de listeye dahil edebiliyor, en
        # az güvenilir seçenek bu yüzden en sona alındı.
        tirnak_ici = re.findall(r'["\u201c\u201d]([^"\u201c\u201d]+)["\u201c\u201d]', text)
        numarali_liste = satirlari_ayikla(text)

        if tirnak_ici:
            gorevler = tirnak_ici
        elif len(numarali_liste) > 1:
            gorevler = numarali_liste
        elif gorevler_match:
            aday = gorevler_match.group(1).strip()
            gorevler = [g.strip() for g in aday.split("|") if g.strip()]
            gorevler = [g for g in gorevler if not _turkce_disi_karakter_var_mi(g)]
        else:
            gorevler = []

        if not gorevler:
            gorevler = [text]  # son çare: tüm cümleyi tek görev olarak al

        ws = get_gorevler_sheet()
        bugun = bugun_str()

        # Aynı bağlam-farkında desen burada da: eklemeden önce mevcut sayıyı al.
        mevcut_satirlar = ws.get_all_values()
        mevcut_sayisi = sum(1 for r in mevcut_satirlar[1:] if r and r[0] == bugun)

        for gorev in gorevler:
            guvenli_append_row(ws, [bugun, "", gorev, "Bekliyor"])

        toplam = mevcut_sayisi + len(gorevler)
        liste = ", ".join(f"'{g}'" for g in gorevler)
        if mevcut_sayisi > 0:
            send_message(f"✅ Mevcut {mevcut_sayisi} bugünkü görevinin üzerine eklendi: {liste}. Toplam {toplam} oldu. Akşam soracağım!")
        else:
            send_message(f"✅ Bugünün görev listesine eklendi: {liste}. Akşam soracağım!")

    else:  # SOHBET
        send_message(cevap)


def main():
    payload_raw = os.environ["CLIENT_PAYLOAD"]
    payload = json.loads(payload_raw)
    update = payload["update"]

    if "update_id" in update:
        save_last_update_id(update["update_id"])
        if update_zaten_islendi_mi(update["update_id"]):
            print(f"Update {update['update_id']} zaten işlenmiş (muhtemelen dinle.py ile çakıştı), atlanıyor.")
            return

    try:
        if "callback_query" in update:
            process_callback(update["callback_query"])
        elif "message" in update:
            process_message(update["message"])
        else:
            print("İşlenecek bir şey yok.")
    except Exception as e:
        # GÜVENLİK AĞI: ne olursa olsun (beklenmedik bir çökme bile),
        # kullanıcı ASLA sessiz kalmamalı. Önceden bu try/except yoktu -
        # bir çökme olursa hem kullanıcıya hiç cevap gitmiyordu hem de
        # (işlendi damgası erken basıldığı için) dinle.py bir daha hiç
        # denemiyordu, mesaj sessizce kayboluyordu.
        import traceback
        hata_logla("handle_update.main (beklenmedik çökme)", traceback.format_exc())
        try:
            send_message("Şu an bunu işleyemedim (teknik bir sorun oldu) — tekrar dener misin?")
        except Exception:
            pass
        print(f"BEKLENMEDİK HATA: {e}")
        return  # işlendi olarak İŞARETLEME - dinle.py tekrar denesin

    if "update_id" in update:
        update_islendi_isaretle(update["update_id"])


if __name__ == "__main__":
    main()
