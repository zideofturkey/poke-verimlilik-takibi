"""
GitHub Actions'ın repository_dispatch (telegram_update) event'i ile
ANINDA tetiklenir. Cloudflare Worker'ın webhook üzerinden ilettiği
güncellemeyi (buton basımı YA DA serbest metin mesaj) işler.
"""

import json
import os
import re
import datetime


def satirlari_ayikla(text):
    """Serbest metinden madde listesi çıkarır: numaralandırmayı temizler,
    boş satırları ve 'Haftalık hedeflerim:' gibi başlık satırlarını (rakamla
    başlamayan, ':' ile biten, kısa satırlar) otomatik ayıklar."""
    maddeler = []
    for satir in text.split("\n"):
        satir = satir.strip()
        if not satir:
            continue
        # Başlık satırı mı? (numarasız, ':' ile bitiyor, kısa)
        if not re.match(r"^\d", satir) and satir.endswith(":") and len(satir) < 40:
            continue
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
            log_to_sheet(isim, "Yapıldı", "dünkü eksik telafi edildi")
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
        gorev_metni = ws.cell(satir_no, 3).value
        durum = "Yapıldı" if sonuc == "evet" else "Yapılmadı"
        ws.update_cell(satir_no, 4, durum)
        log_to_sheet(gorev_metni, durum)
        if sonuc == "evet":
            send_message(f"✅ '{gorev_metni}' kaydedildi. Tebrikler!")
        else:
            send_message(f"Sorun değil, '{gorev_metni}' için yarın devam edelim 👍")


def _sorguyu_cevapla(text):
    """Kullanıcı bir şey sorguladığında (ör. 'bugünkü görevlerimi hatırlatır
    mısın') GERÇEK veriyi Sheets'ten okuyup, SLM'e sadece bu veriyi doğal
    dile çevirtir. Model veride olmayan hiçbir şey uydurmamalı."""
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

    satirlar = []
    if gorevler:
        satirlar.append("Bugünkü ad-hoc görevler:")
        for r in gorevler:
            satirlar.append(f"- {r['GorevMetni']}: {r['Durum']}")
    if takip_bugun:
        satirlar.append("Bugünkü rutin durumu:")
        for r in takip_bugun:
            satirlar.append(f"- {r['Görev']}: {r['Durum']}")
    veri_metni = "\n".join(satirlar)

    prompt = (
        "Sen bir verimlilik takip botusun (adın Poke). Kullanıcı sana bir "
        f"soru sordu: \"{text}\"\n\n"
        "Aşağıda GERÇEK, güncel veri var. SADECE bu veriye dayanarak kısa "
        "ve doğal bir Türkçe cevap ver. Veride olmayan hiçbir şeyi UYDURMA, "
        "sadece verilenleri özetle. SADECE cevabı yaz, başka açıklama ekleme.\n\n"
        f"Veri:\n{veri_metni}"
    )
    try:
        cevap = slm_sorgula(prompt)
        if turkce_disi_karakter_var_mi(cevap):
            raise ValueError("dil kayması")
    except Exception as e:
        print(f"SLM hatası (sorgula): {e}")
        cevap = veri_metni  # yedek: en azından ham veriyi doğru göster

    send_message(cevap)


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
        "CEVAP: <kullanıcıya vereceğin kısa (1 cümle), doğal, samimi Türkçe "
        "yanıt - SADECE Türkçe ve Latin alfabesi kullan, başka dil/alfabe YASAK>"
    )

    try:
        sonuc = slm_sorgula(prompt)
    except Exception as e:
        print(f"SLM hatası (sınıflandırma): {e}")
        send_message("Şu an bunu işleyemedim (teknik bir sorun oldu) — tekrar dener misin?")
        return

    tip_match = re.search(r"TIP:\s*(\w+)", sonuc)
    gorevler_match = re.search(r"GOREVLER:\s*(.+)", sonuc)
    cevap_match = re.search(r"CEVAP:\s*(.+)", sonuc, re.DOTALL)
    tip = tip_match.group(1).upper() if tip_match else "SOHBET"
    cevap = cevap_match.group(1).strip() if cevap_match else "Not aldım 👍"
    if _turkce_disi_karakter_var_mi(cevap):
        cevap = "Not aldım 👍"

    if tip == "GUNLUK_GOREV":
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

    if "callback_query" in update:
        process_callback(update["callback_query"])
    elif "message" in update:
        process_message(update["message"])
    else:
        print("İşlenecek bir şey yok.")


if __name__ == "__main__":
    main()
