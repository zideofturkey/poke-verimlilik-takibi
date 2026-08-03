"""
[MULTI-AGENT ROL: DEĞERLENDİRİCİ + KOÇ + RAPOR — üç rol bu dosyada birleşiyor]
- Değerlendirici: istatistik_cikar() ham veriyi (Takip) örüntüye çevirir
- Koç: koc_onerisi_sun() örüntüye göre öneri sunar, SLM ile kişiselleştirir,
  onay ister ama BURADA karar uygulanmaz - onay handle_update.py'de işlenir
- Rapor: haftalık özet mesajı, verinin insan-okunabilir hâle gelmesi

Haftalık SLM analizi. Takip sekmesindeki son 7 günün verisini toplar,
GitHub Actions runner'ında geçici olarak çalışan yerel bir Ollama modeline
gönderir, çıkan doğal-dil özeti Telegram'a yollar.

Not: Bu model GERÇEK anlamda "on-premise" değildir - GitHub Actions'ın
geçici bulut runner'ında, her çalıştırmada ayağa kaldırılıp kapatılır.
Bu tercih bilinçli yapıldı: gerçek bir yerel/7-24 açık cihaz gerektirmeden
(ki bu "laptop hep açık kalsın" sorununu geri getirirdi) sürdürülebilir,
otomatik bir sistem kurmak için. Detaylar için Sistem Dokümantasyonu'na bakınız.
"""

import re
import hashlib
import datetime
from common import (
    get_sheet, send_message, slm_sorgula, get_aktif_rutinler, rutin_serisi_hesapla,
    turkce_disi_karakter_var_mi, SLM_MODEL_KALITELI, TR_TZ,
    get_gorevler_sheet, get_haftalik_sheet, get_aktif_haftalik_rutinler,
    get_haftalik_rutin_takip_sheet, haftalik_rutin_serisi_hesapla,
    sureyi_dakikaya_cevir, sosyal_medya_limit_dakika, get_deger, set_deger,
)

ANALIZ_GUN_SAYISI = 7
KOC_DURAKLAMA_ESIGI = 5  # kaç gün üst üste kaçırılırsa duraklatma önerilsin

# --- Genişletilmiş Koç eşikleri (kullanıcının isteğiyle eklendi) ---
HAFTALIK_KOC_DURAKLAMA_ESIGI = 3    # kaç HAFTA üst üste kaçırılırsa (haftalık rutin)
HAFTALIK_HEDEF_ORUNTU_ESIGI = 2     # aynı hedef kaç FARKLI haftada Yapılmadı/Süresi Doldu olursa
SURESI_DOLAN_ORUNTU_ESIGI = 3       # aynı anahtar kelime kaç kez Süresi Doldu görevde geçerse
TEKRAR_GOREV_ESIGI = 3              # aynı görev metni kaç farklı kez elle eklenirse
BOSA_VAKIT_ASIM_GUN_ESIGI = 4       # son 10 günde kaç gün sınır aşılırsa
TELAFI_ORUNTU_ESIGI = 3             # bir rutin son 14 günde kaç kez telafi ile tamamlanırsa


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
    cümleler kurmasını) önlemek için. 'Boşa geçen vakit' beyanları
    bu istatistiğe DAHIL EDİLMEZ (o bir rutin değil, serbest metin
    beyanı - ayrıca ele alınır, bkz. bosa_vakit_beyanlarini_topla)."""
    sayaclar = {}
    for r in veriler:
        gorev = r["Görev"]
        if gorev == "Boşa geçen vakit":
            continue
        durum = r["Durum"]
        if gorev not in sayaclar:
            sayaclar[gorev] = {"Yapıldı": 0, "Yapılmadı": 0, "Telafi": 0}
        if durum in sayaclar[gorev]:
            sayaclar[gorev][durum] += 1
    return sayaclar


def bosa_vakit_beyanlarini_topla(veriler):
    """Kullanıcının serbest metinle yazdığı 'boşa geçen vakit'
    beyanlarını (varsa) toplar - haftalık özette gerçekten kullanılsın diye."""
    return [r["Detay"] for r in veriler if r.get("Görev") == "Boşa geçen vakit" and r.get("Detay")]


def prompt_olustur(veriler):
    if not veriler:
        return None

    sayaclar = istatistik_cikar(veriler)
    satirlar = "\n".join(
        f"- {gorev}: {s['Yapıldı']} kez zamanında yapıldı, {s['Telafi']} kez "
        f"gecikmeli telafi edildi, {s['Yapılmadı']} kez hiç yapılmadı"
        for gorev, s in sayaclar.items()
    )

    beyanlar = bosa_vakit_beyanlarini_topla(veriler)
    beyan_blok = ""
    if beyanlar:
        beyan_metni = "\n".join(f"- {b}" for b in beyanlar)
        beyan_blok = (
            "\n\nKullanıcının bu hafta 'boşa geçen vakit' hakkında kendi "
            f"yazdığı beyanlar (varsa bunlara da kısaca değin, bir örüntü "
            f"görüyorsan belirt):\n{beyan_metni}"
        )

    return (
        "Aşağıda bir kişinin son 7 günlük verimlilik istatistiği var. "
        "SADECE verilen sayılara ve beyanlara dayanarak, 3-4 cümlelik akıcı ve "
        "tutarlı bir Türkçe özet yaz. Birbirini çelişen ifadeler kullanma. "
        "En yüksek 'yapıldı' oranına sahip görev(ler)i öv, en yüksek "
        "'yapılmadı' oranına sahip görev(ler)i nazikçe hatırlat. "
        "Sadece özeti yaz, başka açıklama, başlık ya da giriş cümlesi ekleme.\n\n"
        f"İstatistik:\n{satirlar}{beyan_blok}"
    )


def _slm_koc_mesaji(prompt, yedek_mesaj):
    """Koç önerilerinin ortak SLM-kişiselleştirme deseni - 6 farklı öneri
    türü de bunu kullanıyor. SLM hata verirse ya da dil kayması olursa,
    sabit ama hâlâ anlamlı bir yedek mesaja düşülüyor - kullanıcı asla
    hiçbir cevap almadan kalmıyor."""
    try:
        mesaj = slm_sorgula(prompt, model=SLM_MODEL_KALITELI)
        if turkce_disi_karakter_var_mi(mesaj):
            raise ValueError("dil kayması tespit edildi")
        return mesaj
    except Exception as e:
        print(f"SLM hatası (koç önerisi): {e}")
        return yedek_mesaj


def koc_onerisi_sun():
    """Sürekli kaçırılan GÜNLÜK rutinler için duraklatma önerisi sunar.
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
            mesaj = _slm_koc_mesaji(prompt, (
                f"🧑‍🏫 '{rutin['isim']}' rutinini {miss_streak} gündür "
                "kaçırıyorsun. Bir süreliğine duraklatalım mı?"
            ))
            send_message(
                mesaj,
                buttons=[
                    [
                        {"text": "✅ Evet, duraklat", "callback_data": f"koc_duraklat_{rutin['id']}_evet"},
                        {"text": "❌ Hayır, devam", "callback_data": f"koc_duraklat_{rutin['id']}_hayir"},
                    ]
                ],
            )


def haftalik_rutin_onerisi_sun():
    """GENİŞLETME 1/5: koc_onerisi_sun'ın HAFTALIK rutinler (Oda tozu
    alma vb.) için eşleniği - aynı desen, günler yerine haftalar."""
    for rutin in get_aktif_haftalik_rutinler():
        _, miss_streak = haftalik_rutin_serisi_hesapla(rutin["isim"])
        if miss_streak >= HAFTALIK_KOC_DURAKLAMA_ESIGI:
            prompt = (
                "Sen bir verimlilik koçu botusun (adın Poke). Kullanıcı "
                f"'{rutin['isim']}' HAFTALIK rutinini {miss_streak} haftadır "
                "üst üste kaçırıyor. Ona bunu nazikçe belirt ve bir "
                "süreliğine bu rutini duraklatmayı önererek onay iste. "
                "Kısa (2-3 cümle), samimi. SADECE mesajı yaz."
            )
            mesaj = _slm_koc_mesaji(prompt, (
                f"🧑‍🏫 '{rutin['isim']}' haftalık rutinini {miss_streak} "
                "haftadır kaçırıyorsun. Bir süreliğine duraklatalım mı?"
            ))
            send_message(
                mesaj,
                buttons=[[
                    {"text": "✅ Evet, duraklat", "callback_data": f"kochaftarutin_{rutin['id']}_evet"},
                    {"text": "❌ Hayır, devam", "callback_data": f"kochaftarutin_{rutin['id']}_hayir"},
                ]],
            )


def haftalik_hedef_oruntu_sun():
    """GENİŞLETME 2/5: aynı (ya da neredeyse aynı metinli) haftalık hedef,
    birden fazla FARKLI haftada 'Yapılmadı'/'Süresi Doldu' olarak
    işaretlenmişse, Koç bunu fark edip birlikte gözden geçirmeyi önerir.
    Hedefler serbest metin olduğu için basit metin normalizasyonuyla
    (küçük harf + boşluk temizliği) gruplanıyor - kelime kelime aynı
    yazılmışsa yakalar, çok farklı ifade edilmişse yakalamayabilir."""
    ws = get_haftalik_sheet()
    rows = ws.get_all_records()
    kotu_haftalar = {}  # normalize metin -> {hafta seti}
    orijinal_metin = {}
    for r in rows:
        if r.get("Durum") not in ("Yapılmadı", "Süresi Doldu"):
            continue
        metin = (r.get("HedefMetni") or "").strip()
        if not metin:
            continue
        norm = metin.lower()
        kotu_haftalar.setdefault(norm, set()).add(r.get("HaftaBaslangic"))
        orijinal_metin.setdefault(norm, metin)

    for norm, haftalar in kotu_haftalar.items():
        if len(haftalar) < HAFTALIK_HEDEF_ORUNTU_ESIGI:
            continue
        metin = orijinal_metin[norm]
        hash6 = hashlib.sha1(norm.encode()).hexdigest()[:6]
        set_deger(f"koc_pending_{hash6}", metin)
        prompt = (
            "Sen bir verimlilik koçu botusun (adın Poke). Kullanıcının "
            f"'{metin}' haftalık hedefi son {len(haftalar)} farklı haftada "
            "tutturulamadı. Bunu yargılamadan fark ettir, hedefi birlikte "
            "gözden geçirmek (belki daha ulaşılabilir hâle getirmek) "
            "isteyip istemediğini nazikçe sor. Kısa (2-3 cümle). SADECE mesajı yaz."
        )
        mesaj = _slm_koc_mesaji(prompt, (
            f"🧑‍🏫 '{metin}' hedefini son {len(haftalar)} haftadır "
            "tutturamıyorsun. Bunu birlikte gözden geçirelim mi?"
        ))
        send_message(
            mesaj,
            buttons=[[
                {"text": "✅ Evet, konuşalım", "callback_data": f"kochedef_{hash6}_evet"},
                {"text": "❌ Hayır, aynen kalsın", "callback_data": f"kochedef_{hash6}_hayir"},
            ]],
        )
        break  # bir seferde tek öneri - spam olmasın


def suresi_dolan_oruntu_sun():
    """GENİŞLETME 3/5: 'Süresi Doldu' (cevapsız kalıp otomatik süresi
    dolan) günlük görevlerin metinlerinde tekrar eden bir anahtar kelime
    varsa (ör. hep 'araştırma' içeren görevler cevapsız kalıyorsa), Koç
    bu örüntüyü fark edip konuşmayı önerir."""
    ws = get_gorevler_sheet()
    rows = ws.get_all_records()
    suresi_dolanlar = [r["GorevMetni"] for r in rows if r.get("Durum") == "Süresi Doldu"]
    if len(suresi_dolanlar) < SURESI_DOLAN_ORUNTU_ESIGI:
        return

    durak_kelimeler = {"için", "olan", "gibi", "yapma", "kontrol", "kaydet", "listesi"}
    kelime_sayaci = {}
    kelime_orneklari = {}
    for metin in suresi_dolanlar:
        kelimeler = {w.lower() for w in re.findall(r"[a-zA-ZçğıöşüÇĞİÖŞÜ]+", metin) if len(w) > 3}
        for k in kelimeler:
            k_kucuk = k.lower()
            if k_kucuk in durak_kelimeler:
                continue
            kelime_sayaci[k_kucuk] = kelime_sayaci.get(k_kucuk, 0) + 1
            kelime_orneklari.setdefault(k_kucuk, [])
            if metin not in kelime_orneklari[k_kucuk]:
                kelime_orneklari[k_kucuk].append(metin)

    for kelime, sayi in sorted(kelime_sayaci.items(), key=lambda x: -x[1]):
        if sayi < SURESI_DOLAN_ORUNTU_ESIGI:
            continue
        ornekler = kelime_orneklari[kelime][:3]
        hash6 = hashlib.sha1(kelime.encode()).hexdigest()[:6]
        set_deger(f"koc_pending_{hash6}", kelime)
        ornek_metni = ", ".join(f"'{o}'" for o in ornekler)
        prompt = (
            "Sen bir verimlilik koçu botusun (adın Poke). Kullanıcının "
            f"son dönemde '{kelime}' kelimesini içeren {sayi} görevi hiç "
            f"cevaplanmadan süresi doldu (örnekler: {ornek_metni}). Bunu "
            "nazikçe fark ettir, bu tür görevleri daha küçük parçalara "
            "bölmeyi ya da farklı bir yaklaşım denemeyi konuşmak isteyip "
            "istemediğini sor. Kısa (2-3 cümle), yargılamadan. SADECE mesajı yaz."
        )
        mesaj = _slm_koc_mesaji(prompt, (
            f"🧑‍🏫 '{kelime}' kelimesi geçen {sayi} görevin süresi cevapsız "
            "kaldığı için doldu. Bu tür görevleri konuşalım mı?"
        ))
        send_message(
            mesaj,
            buttons=[[
                {"text": "✅ Evet, konuşalım", "callback_data": f"kocsuresidolan_{hash6}_evet"},
                {"text": "❌ Hayır, gerek yok", "callback_data": f"kocsuresidolan_{hash6}_hayir"},
            ]],
        )
        break  # bir seferde tek öneri


def tekrarlanan_gorev_oruntu_sun():
    """GENİŞLETME 4/5: aynı ad-hoc görev metni (ör. 'kitap oku') birden
    çok farklı günde elle eklenmişse, Koç bunu kalıcı bir rutine
    dönüştürmeyi önerir - kullanıcı her seferinde elle yazmak zorunda
    kalmasın diye. Zaten aktif bir rutinle aynı isimdeyse önerilmez."""
    ws = get_gorevler_sheet()
    rows = ws.get_all_records()
    aktif_rutin_isimleri = {r["isim"].strip().lower() for r in get_aktif_rutinler()}

    metin_gunleri = {}  # normalize metin -> {tarih seti}
    orijinal_metin = {}
    for r in rows:
        metin = (r.get("GorevMetni") or "").strip()
        if not metin:
            continue
        norm = metin.lower()
        if norm in aktif_rutin_isimleri:
            continue
        metin_gunleri.setdefault(norm, set()).add(r.get("Tarih"))
        orijinal_metin.setdefault(norm, metin)

    for norm, gunler in metin_gunleri.items():
        if len(gunler) < TEKRAR_GOREV_ESIGI:
            continue
        metin = orijinal_metin[norm]
        hash6 = hashlib.sha1(norm.encode()).hexdigest()[:6]
        set_deger(f"koc_pending_{hash6}", metin)
        prompt = (
            "Sen bir verimlilik koçu botusun (adın Poke). Kullanıcı "
            f"'{metin}' görevini {len(gunler)} farklı günde elle tekrar "
            "eklemiş. Bunu kalıcı bir günlük rutine dönüştürmeyi öner - "
            "böylece her seferinde elle yazmak zorunda kalmaz. Kısa (2-3 "
            "cümle), samimi. SADECE mesajı yaz."
        )
        mesaj = _slm_koc_mesaji(prompt, (
            f"🧑‍🏫 '{metin}' görevini {len(gunler)} kez elle eklemişsin. "
            "Bunu kalıcı bir günlük rutin yapalım mı?"
        ))
        send_message(
            mesaj,
            buttons=[[
                {"text": "✅ Evet, rutin yap", "callback_data": f"kocgorevrutin_{hash6}_evet"},
                {"text": "❌ Hayır, böyle kalsın", "callback_data": f"kocgorevrutin_{hash6}_hayir"},
            ]],
        )
        break  # bir seferde tek öneri


def bosa_vakit_trend_sun():
    """GENİŞLETME 5/5 (a): son 10 günde kullanıcı, güncel sosyal medya
    sınırını (Durum sekmesinde tutulan, artık dinamik) birden çok kez
    aştıysa, Koç sınırı biraz daha sıkı bir değere çekmeyi önerir -
    yalnızca kullanıcı onaylarsa sınır gerçekten değişir."""
    ws = get_sheet()
    rows = ws.get_all_records()
    limit = sosyal_medya_limit_dakika()
    bugun = datetime.datetime.now(TR_TZ).date()
    sinir = bugun - datetime.timedelta(days=10)

    asan_gun_sayisi = 0
    for r in rows:
        if r.get("Görev") != "Boşa geçen vakit":
            continue
        try:
            tarih = datetime.datetime.strptime(r["Tarih"], "%Y-%m-%d").date()
        except (ValueError, KeyError):
            continue
        if tarih < sinir:
            continue
        dakika = sureyi_dakikaya_cevir(r.get("Detay") or "")
        if dakika is not None and dakika > limit:
            asan_gun_sayisi += 1

    if asan_gun_sayisi < BOSA_VAKIT_ASIM_GUN_ESIGI:
        return

    onerilen_limit = max(30, limit - 15)
    prompt = (
        "Sen bir verimlilik koçu botusun (adın Poke). Kullanıcı son 10 "
        f"günde {asan_gun_sayisi} kez, kendi belirlediği günlük "
        f"{limit} dakikalık sosyal medya/boşa vakit sınırını aştı. Bunu "
        f"yargılamadan fark ettir, sınırı {onerilen_limit} dakikaya "
        "düşürmeyi önererek onay iste. Kısa (2-3 cümle), destekleyici. "
        "SADECE mesajı yaz."
    )
    mesaj = _slm_koc_mesaji(prompt, (
        f"🧑‍🏫 Son 10 günde {asan_gun_sayisi} kez {limit} dakikalık "
        f"sınırını aştın. Sınırı {onerilen_limit} dakikaya düşürelim mi?"
    ))
    send_message(
        mesaj,
        buttons=[[
            {"text": f"✅ Evet, {onerilen_limit} dk yap", "callback_data": f"kocbosavakit_{onerilen_limit}_evet"},
            {"text": "❌ Hayır, aynı kalsın", "callback_data": f"kocbosavakit_{onerilen_limit}_hayir"},
        ]],
    )


def telafi_oruntu_sun():
    """GENİŞLETME 5/5 (b): bir günlük rutin son 14 günde birkaç kez
    'Telafi' (zamanında değil, ertesi gün gecikmeli) ile tamamlanmışsa,
    Koç hatırlatma saatinin değiştirilmesini konuşmayı önerir. NOT: şu an
    per-rutin özel bir hatırlatma saati sistemi yok - bu öneri kabul
    edilirse somut bir sonraki adım (örn. hatırlatma saatlerini gözden
    geçirme) için bir sohbet başlatıyor, otomatik bir saat değişikliği
    yapmıyor (böyle bir mekanizma henüz yok)."""
    ws = get_sheet()
    rows = ws.get_all_records()
    bugun = datetime.datetime.now(TR_TZ).date()
    sinir = bugun - datetime.timedelta(days=14)

    for rutin in get_aktif_rutinler():
        telafi_sayisi = 0
        for r in rows:
            if r.get("Görev") != rutin["isim"] or r.get("Durum") != "Telafi":
                continue
            try:
                tarih = datetime.datetime.strptime(r["Tarih"], "%Y-%m-%d").date()
            except (ValueError, KeyError):
                continue
            if tarih >= sinir:
                telafi_sayisi += 1

        if telafi_sayisi < TELAFI_ORUNTU_ESIGI:
            continue

        prompt = (
            "Sen bir verimlilik koçu botusun (adın Poke). Kullanıcı "
            f"'{rutin['isim']}' rutinini son 14 günde {telafi_sayisi} kez "
            "zamanında değil, ertesi gün telafi ederek tamamlamış. Bunu "
            "nazikçe fark ettir, hatırlatma saatinin ona uygun olup "
            "olmadığını konuşmayı öner. Kısa (2-3 cümle). SADECE mesajı yaz."
        )
        mesaj = _slm_koc_mesaji(prompt, (
            f"🧑‍🏫 '{rutin['isim']}' rutinini son 14 günde {telafi_sayisi} "
            "kez ancak ertesi gün telafi edebilmişsin. Hatırlatma saatini "
            "konuşalım mı?"
        ))
        send_message(
            mesaj,
            buttons=[[
                {"text": "✅ Evet, konuşalım", "callback_data": f"koctelafi_{rutin['id']}_evet"},
                {"text": "❌ Hayır, böyle iyi", "callback_data": f"koctelafi_{rutin['id']}_hayir"},
            ]],
        )
        break  # bir seferde tek öneri


def koc_onerilerini_calistir():
    """[MULTI-AGENT ROL: KOÇ] Tüm örüntü tespit mekanizmalarını sırayla
    çalıştırır - her biri kendi eşiğine göre bağımsız karar verir, hiçbiri
    diğerini engellemez. Kullanıcının isteğiyle 5 yeni mekanizma eklendi
    (haftalık rutin/hedef, süresi dolan örüntüsü, tekrarlanan görev,
    boşa vakit trend, telafi örüntüsü) - eskisi (günlük rutin duraklama)
    hâlâ ilk sırada."""
    koc_onerisi_sun()
    haftalik_rutin_onerisi_sun()
    haftalik_hedef_oruntu_sun()
    suresi_dolan_oruntu_sun()
    tekrarlanan_gorev_oruntu_sun()
    bosa_vakit_trend_sun()
    telafi_oruntu_sun()


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

    koc_onerilerini_calistir()


if __name__ == "__main__":
    main()
