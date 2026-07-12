"""
GitHub Actions'ın repository_dispatch (telegram_update) event'i ile
ANINDA tetiklenir. Cloudflare Worker'ın webhook üzerinden ilettiği
güncellemeyi (buton basımı YA DA serbest metin mesaj) işler.
"""

import json
import os
import re
import datetime
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
    RUTINLER,
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
        rutin = next((r for r in RUTINLER if r["id"] == rutin_id), None)
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


def process_message(message):
    text = message.get("text", "").strip()
    if not text:
        return

    bekleyen = get_bekleyen_soru()

    if bekleyen == "gunluk_gorev":
        gorevler = []
        for satir in text.split("\n"):
            satir = satir.strip()
            # Baştaki "1.", "1)", "1-" gibi numaralandırmayı temizle
            satir = re.sub(r"^\d+[\.\)\-]?\s*", "", satir)
            if satir:
                gorevler.append(satir)

        if not gorevler:
            send_message("Boş görünüyor, en az bir satıra görev yazman lazım 🙂")
            return

        ws = get_gorevler_sheet()
        bugun = bugun_str()
        for gorev in gorevler:
            ws.append_row([bugun, "", gorev, "Bekliyor"])
        set_bekleyen_soru("")
        liste = "\n".join(f"{i+1}) {g}" for i, g in enumerate(gorevler))
        send_message(f"Not aldım, bugünkü görevlerin:\n{liste}\n\nAkşam bunları soracağım!")

    elif bekleyen == "haftalik_hedef":
        hedefler = []
        for satir in text.split("\n"):
            satir = satir.strip()
            satir = re.sub(r"^\d+[\.\)\-]?\s*", "", satir)
            if satir:
                hedefler.append(satir)

        if not hedefler:
            send_message("Boş görünüyor, en az bir satıra hedef yazman lazım 🙂")
            return

        ws = get_haftalik_sheet()
        hafta = hafta_baslangic_str()
        for hedef in hedefler:
            ws.append_row([hafta, hedef, "Bekliyor"])
        set_bekleyen_soru("")
        liste = "\n".join(f"{i+1}) {h}" for i, h in enumerate(hedefler))
        send_message(f"Haftalık hedeflerin kaydedildi:\n{liste}\n\nHafta ortasında kontrol edeceğim. 📝")

    elif bekleyen == "bosa_vakit":
        log_to_sheet("Boşa geçen vakit", "Beyan", text)
        set_bekleyen_soru("")

        prompt = (
            "Sen bir verimlilik koçu asistanısın (adın Poke). Kullanıcı akşam "
            f"check-in'inde şunu yazdı:\n\n\"{text}\"\n\n"
            "Görevlerin:\n"
            "1. Eğer cümlede bir soru varsa, kısa ve yararlı şekilde cevapla.\n"
            "2. Kısa (1-2 cümle), samimi, doğal bir Türkçe yanıt yaz - "
            "robotik bir onay cümlesi değil, gerçek bir konuşma gibi.\n"
            "Sadece kullanıcıya gönderilecek yanıtı yaz, başka açıklama ekleme."
        )
        try:
            cevap = slm_sorgula(prompt)
            if _turkce_disi_karakter_var_mi(cevap):
                cevap = "Not edildi, teşekkürler 📝"
        except Exception as e:
            print(f"SLM hatası (bosa_vakit): {e}")
            cevap = "Not edildi, teşekkürler 📝"

        send_message(cevap)

    else:
        _niyet_tespit_et_ve_isle(text)


def _turkce_disi_karakter_var_mi(metin):
    """Çince, Arapça, Kiril vb. beklenmedik alfabelerden karakter olup
    olmadığını kontrol eder - model 'dil kayması' yaşarsa yakalamak için."""
    for ch in metin:
        kod = ord(ch)
        # Temel Latin + Türkçe özel karakterler + yaygın noktalama/rakam dışında
        # bir şey varsa (ör. CJK, Kiril, Arapça aralıkları) şüpheli say.
        if kod > 0x2FF and kod not in (0x2018, 0x2019, 0x201C, 0x201D, 0x2026):
            return True
    return False


def _niyet_tespit_et_ve_isle(text):
    """Bekleyen bir soru yokken gelen serbest metni işler: bu bir görev
    ekleme isteği mi (ör. 'bugün X yapacağım da ekleyeyim'), yoksa genel
    bir sohbet/soru mu - SLM'e ayırt ettirir."""
    prompt = (
        "Sen bir verimlilik takip botusun (adın Poke). Kullanıcı sana şunu "
        f"yazdı:\n\n\"{text}\"\n\n"
        "Eğer bu mesaj kullanıcının BUGÜN için yeni bir görev/yapılacak iş "
        "eklemek istediğini ifade ediyorsa, SADECE şu formatta cevap ver "
        "(başka hiçbir şey ekleme):\n"
        "GOREV: <görevin kısa ve net hali>\n\n"
        "Eğer görev eklemekle ilgili değilse (sohbet, soru, yorum vb.), "
        "SADECE şu formatta cevap ver:\n"
        "SOHBET: <kullanıcıya vereceğin kısa (1-2 cümle), doğal, samimi "
        "Türkçe cevap>\n\n"
        "ÖNEMLİ: Kullanıcı hangi dilde yazarsa yazsın (Türkçe, İngilizce, "
        "vb.), SEN her zaman SADECE Türkçe ve Latin alfabesiyle cevap ver. "
        "Çince, Arapça, Kiril veya başka bir alfabe/dil KESİNLİKLE KULLANMA. "
        "Başka hiçbir açıklama ekleme, sadece bu iki formattan birini kullan."
    )

    try:
        cevap = slm_sorgula(prompt)
    except Exception as e:
        print(f"SLM hatası (niyet tespiti): {e}")
        send_message(
            "Şu an bunu işleyemedim (teknik bir sorun oldu) — istersen "
            "tekrar dener misin?"
        )
        return

    if cevap.startswith("GOREV:"):
        gorev_metni = cevap.replace("GOREV:", "", 1).strip()
        if _turkce_disi_karakter_var_mi(gorev_metni):
            print(f"Model beklenmedik alfabe üretti, orijinal metne dönülüyor: {gorev_metni!r}")
            gorev_metni = text  # güvenlik ağı: modelin bozuk çıktısı yerine kullanıcının kendi metnini kullan
        ws = get_gorevler_sheet()
        ws.append_row([bugun_str(), "", gorev_metni, "Bekliyor"])
        send_message(f"✅ Bugünün görev listesine eklendi: '{gorev_metni}'. Akşam soracağım!")
    elif cevap.startswith("SOHBET:"):
        cevap_metni = cevap.replace("SOHBET:", "", 1).strip()
        if _turkce_disi_karakter_var_mi(cevap_metni):
            cevap_metni = "Not aldım 👍"
        send_message(cevap_metni)
    else:
        # Model beklenen formatı kullanmadıysa, olduğu gibi gönder
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
