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
    """Serbest metinden madde listesi çıkarır. Kural: eğer mesajda numaralı
    satır(lar) varsa, SADECE numaralı satırlar madde sayılır - başlık,
    giriş cümlesi ya da başka herhangi bir numarasız satır (ör. 'Günaydın,
    bugünün görevlerini yazıyorum') otomatik göz ardı edilir. Numaralı
    satır HİÇ yoksa (düz, numarasız liste), tüm dolu satırlar madde sayılır."""
    satirlar_ham = [s.strip() for s in text.split("\n") if s.strip()]
    numarali_var = any(re.match(r"^\d+[\.\)\-]", s) for s in satirlar_ham)

    maddeler = []
    for satir in satirlar_ham:
        numarali_mi = re.match(r"^\d+[\.\)\-]?\s*", satir)
        if numarali_var and not numarali_mi:
            continue  # numaralı liste varsa, numarasız satırlar (başlık/giriş) elenir
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
    log_slm_karari,
    get_aktif_rutinler,
    get_sheet,
    get_rutinler_sheet,
    rutin_serisi_hesapla,
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
        # format: rutin_<id>_evet / rutin_<id>_hayir / rutin_<id>_telafi
        # <id> kendisi alt çizgi içerebilir (ör. "sabah_telefon"), bu yüzden
        # sondan ayırıyoruz: ilk parça "rutin", son parça sonuç, arası id.
        parcalar = callback_data.split("_")
        sonuc = parcalar[-1]
        rutin_id = "_".join(parcalar[1:-1])
        rutin = next((r for r in get_aktif_rutinler() if r["id"] == rutin_id), None)
        isim = rutin["isim"] if rutin else rutin_id
        if sonuc == "evet":
            log_to_sheet(isim, "Yapıldı")
            send_message(f"✅ '{isim}' kaydedildi. Tebrikler!")
        elif sonuc == "hayir":
            log_to_sheet(isim, "Yapılmadı")
            send_message(f"Sorun değil, '{isim}' için yarın devam edelim 👍")
        elif sonuc == "telafi":
            log_to_sheet(isim, "Telafi", "dünkü eksik için bugün telafi edildi")
            send_message(f"🔁 Harika, '{isim}' için dünkü eksik telafi edildi olarak kaydedildi!")
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


def _sorguyu_cevapla(text):
    """Kullanıcı bir şey sorguladığında (ör. 'bugünkü görevlerimi hatırlatır
    mısın') GERÇEK veriyi Sheets'ten okuyup, DOĞRUDAN Python'da (SLM'e
    yazdırmadan) net bir liste hâlinde cevap verir. Bunun iki sebebi var:
    (1) kullanıcı direkt liste formatını daha verimli buluyor,
    (2) SLM serbest metin üretirken bazen yazım hatası yapıyordu (ör.
    'rutin' yerine 'rutün') - deterministik formatlama bunu tamamen ortadan
    kaldırıyor."""
    bugun = bugun_str()

    ws_gorev = get_gorevler_sheet()
    gorevler = [r for r in ws_gorev.get_all_records() if r.get("Tarih") == bugun]

    rutin_isimleri = {r["isim"] for r in get_aktif_rutinler()}
    ws_takip = get_sheet()
    takip_bugun = [
        r for r in ws_takip.get_all_records()
        if r.get("Tarih") == bugun and r.get("Görev") in rutin_isimleri
    ]

    if not gorevler and not takip_bugun:
        send_message("Bugün için henüz kayıtlı bir görev ya da rutin durumu yok.")
        return

    # Kullanıcı sadece eksikleri mi soruyor, yoksa genel durumu mu?
    eksik_kelimeler = ["yapmadığ", "yapmadık", "kaçır", "eksik", "tamamlamadığ", "unuttuğ"]
    sadece_eksikler = any(k in text.lower() for k in eksik_kelimeler)

    satirlar = []
    for r in takip_bugun:
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
            send_message("Harika, bugün için kaçırdığın bir şey görünmüyor! 🎉")
        else:
            send_message("Bugün için henüz kayıtlı bir görev ya da rutin durumu yok.")
        return

    baslik = "Bugün henüz yapmadıkların:" if sadece_eksikler else "Bugünkü durumun:"
    send_message(f"{baslik}\n" + "\n".join(satirlar))


def process_message(message):
    text = message.get("text", "").strip()
    if not text:
        return

    bekleyen = get_bekleyen_soru()
    _siniflandir_ve_isle(text, bekleyen)


_turkce_disi_karakter_var_mi = turkce_disi_karakter_var_mi


BEKLEYEN_ACIKLAMA = {
    "gunluk_gorev": "sabah sorduğum 'bugün ne yapacaksın' sorusu",
    "haftalik_hedef": "pazar günü sorduğum 'bu hafta hedeflerin ne' sorusu",
    "bosa_vakit": "akşam sorduğum 'bugün ne kadar boşa vakit geçirdin' sorusu",
}


def _siniflandir_ve_isle(text, bekleyen):
    """Gelen her serbest metni SLM'e sınıflandırtır. 'bekleyen' sadece bir
    BAĞLAM/ipucu olarak veriliyor - kesin kural değil. Model, mesajın
    içeriğine bakıp en uygun kategoriyi kendisi seçiyor. Bu, katı bir
    durum makinesinin (sabit 'şu an şunu bekliyorum -> öyle işle' mantığının)
    beklenmedik senaryolarda yanlış kategoriye yazması sorununu çözer."""

    baglam = (
        f"Kullanıcıya az önce sorduğum, henüz cevap bekleyen bir soru var: "
        f"{BEKLEYEN_ACIKLAMA.get(bekleyen, bekleyen)}."
        if bekleyen else
        "Şu an kullanıcıya sorduğum, cevap beklediğim bir soru yok."
    )

    aktif_rutinler = get_aktif_rutinler()
    rutin_isim_listesi = ", ".join(f"'{r['isim']}'" for r in aktif_rutinler)

    prompt = (
        "Sen bir verimlilik takip botusun (adın Poke). "
        f"{baglam}\n\n"
        f"Kullanıcı şunu yazdı:\n\"{text}\"\n\n"
        "Bu mesajı aşağıdaki kategorilerden EN UYGUN olanına ata "
        "(bekleyen soru sadece bir ipucu, mesajın gerçek içeriğine göre "
        "karar ver - biri başka bir konuda yazmış olabilir):\n"
        "- GUNLUK_GOREV: bugün için yapılacaklar listesi veriyor\n"
        "- HAFTALIK_HEDEF: bu haftanın hedeflerini veriyor\n"
        "- BOSA_VAKIT: bugün ne kadar boşa vakit geçirdiğini anlatıyor\n"
        "- YENI_GOREV: herhangi bir an kendiliğinden yeni görev/iş ekliyor. "
        "Kullanıcı genelde eklenecek görev(ler)i tırnak içinde yazar, "
        "ör: 'bugüne şunu ekliyorum: \"kitap oku\", \"spor yap\"' - birden "
        "fazla görev aynı mesajda olabilir\n"
        f"- RUTIN_TAMAMLA: kullanıcı şu sabit rutinlerden birini tamamladığını "
        f"bildiriyor: {rutin_isim_listesi}. Ör: 'Fransızca rutinimi tamamladım', "
        "'bugün spor yaptım' gibi doğal cümleler. YENI_GOREV ile KARIŞTIRMA - "
        "bu kategori sadece yukarıdaki listedeki rutinler için\n"
        "- SORGULA: kullanıcı bir şeyi EKLEMİYOR, var olan bilgiyi SORUYOR/"
        "HATIRLATMAMI istiyor. Ör: 'bugünkü görevlerimi hatırlatır mısın', "
        "'bu hafta hedeflerim neydi', 'hangi rutinleri kaçırdım'. Bu ifadelerde "
        "'görev'/'hedef' kelimesi geçebilir ama YENI_GOREV ile KARIŞTIRMA - "
        "kullanıcı bir şey eklemiyor, sorguluyor\n"
        "- SOHBET: yukarıdakilerin hiçbiriyle ilgili değil, genel sohbet/soru\n\n"
        "SADECE şu formatta cevap ver, başka hiçbir şey ekleme:\n"
        "TIP: <KATEGORI>\n"
        "GOREVLER: <SADECE TIP=YENI_GOREV ise: her görevi \" | \" ile "
        "ayırarak yaz (tırnak işaretleri olmadan). Diğer TIP'lerde boş bırak>\n"
        f"RUTIN: <SADECE TIP=RUTIN_TAMAMLA ise: şu listeden BİREBİR aynı "
        f"şekilde yaz, birden fazla rutin tamamlandıysa \" | \" ile ayır: "
        f"{rutin_isim_listesi}. Diğer TIP'lerde boş bırak>\n"
        "CEVAP: <kullanıcıya vereceğin kısa (1-2 cümle), doğal, samimi Türkçe "
        "yanıt - SADECE Türkçe ve Latin alfabesi kullan, başka dil/alfabe YASAK. "
        "TIP=BOSA_VAKIT ise: 'not aldım' gibi genel bir cümle YETERLİ DEĞİL - "
        "kullanıcının ANLATTIĞI şeye (ne yaptığına, ne kadar vakit geçirdiğine) "
        "gerçekten değinen, kısa ama düşünceli bir yorum/gözlem yap."
    )

    try:
        sonuc = slm_sorgula(prompt)
    except Exception as e:
        print(f"SLM hatası (sınıflandırma): {e}")
        send_message("Şu an bunu işleyemedim (teknik bir sorun oldu) — tekrar dener misin?")
        return

    tip_match = re.search(r"TIP:\s*(\w+)", sonuc)
    gorevler_match = re.search(r"GOREVLER:\s*(.+)", sonuc)
    rutin_match = re.search(r"RUTIN:\s*(.+)", sonuc)
    cevap_match = re.search(r"CEVAP:\s*(.+)", sonuc, re.DOTALL)
    tip = tip_match.group(1).upper() if tip_match else "SOHBET"
    cevap = cevap_match.group(1).strip() if cevap_match else "Not aldım 👍"
    if _turkce_disi_karakter_var_mi(cevap):
        cevap = "Not aldım 👍"

    log_slm_karari(tip, text, prompt, sonuc)

    if tip == "RUTIN_TAMAMLA":
        rutin_ham_liste = rutin_match.group(1).strip() if rutin_match else ""
        adaylar = [r.strip().strip("'\"") for r in rutin_ham_liste.split("|") if r.strip()]
        aktif_isimler = {r["isim"] for r in aktif_rutinler}
        eslesenler = [ad for ad in adaylar if ad in aktif_isimler]

        if eslesenler:
            for isim in eslesenler:
                log_to_sheet(isim, "Yapıldı")
            liste = ", ".join(f"'{i}'" for i in eslesenler)
            send_message(f"✅ {liste} tamamlandı olarak kaydedildi. Tebrikler!")
        else:
            send_message(
                "Hangi rutinden bahsettiğini tam anlayamadım — akşam kontrolünde "
                "butonla işaretleyebilirsin, orası her zaman güvenilir çalışır 👍"
            )

    elif tip == "GUNLUK_GOREV":
        gorevler = satirlari_ayikla(text)
        if not gorevler:
            send_message("Bunu görev listesi olarak anlayamadım, satır satır tekrar yazar mısın?")
            return
        ws = get_gorevler_sheet()
        bugun = bugun_str()
        for gorev in gorevler:
            ws.append_row([bugun, "", gorev, "Bekliyor"])
        set_bekleyen_soru("")
        liste = "\n".join(f"{i+1}) {g}" for i, g in enumerate(gorevler))
        send_message(f"Not aldım, bugünkü görevlerin:\n{liste}\n\nAkşam bunları soracağım!")

    elif tip == "HAFTALIK_HEDEF":
        hedefler = satirlari_ayikla(text)
        if not hedefler:
            send_message("Bunu hedef listesi olarak anlayamadım, satır satır tekrar yazar mısın?")
            return
        ws = get_haftalik_sheet()
        hafta = hafta_baslangic_str()
        for hedef in hedefler:
            ws.append_row([hafta, hedef, "Bekliyor"])
        set_bekleyen_soru("")
        liste = "\n".join(f"{i+1}) {h}" for i, h in enumerate(hedefler))
        send_message(f"Haftalık hedeflerin kaydedildi:\n{liste}\n\nHafta ortasında kontrol edeceğim. 📝")

    elif tip == "BOSA_VAKIT":
        log_to_sheet("Boşa geçen vakit", "Beyan", text)
        set_bekleyen_soru("")
        send_message(cevap)

    elif tip == "SORGULA":
        _sorguyu_cevapla(text)

    elif tip == "YENI_GOREV":
        # Tırnak varsa önce deterministik olarak yakala (güvenilir) - model
        # kendi çıkarımını sadece tırnak yokken devreye sokar.
        tirnak_ici = re.findall(r'["\u201c\u201d]([^"\u201c\u201d]+)["\u201c\u201d]', text)
        if tirnak_ici:
            gorevler = tirnak_ici
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
        for gorev in gorevler:
            ws.append_row([bugun, "", gorev, "Bekliyor"])
        liste = ", ".join(f"'{g}'" for g in gorevler)
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

    if "callback_query" in update:
        process_callback(update["callback_query"])
    elif "message" in update:
        process_message(update["message"])
    else:
        print("İşlenecek bir şey yok.")


if __name__ == "__main__":
    main()
