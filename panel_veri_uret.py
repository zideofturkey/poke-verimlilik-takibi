"""
[MULTI-AGENT ROL: RAPOR (Reporter) - veri üretme tarafı]
Panel'in tükettiği panel/data.json dosyasını üretir. Kişisel sekme
tamamen gerçek Sheets verisine dayanır. Teknik sekmede workflow geçmişi
GitHub API'den gerçek veri çeker; SLM ham prompt/cevap logu artık
tutuluyor (bkz. common.py: log_slm_karari) ama sadece bu özelliğin
eklendiği tarihten sonrası için - geçmişe dönük veri yoktur.
"""

import json
import os
import datetime
import requests
from common import (
    get_sheet,
    get_gorevler_sheet,
    get_haftalik_sheet,
    get_aktif_rutinler,
    get_aktif_haftalik_rutinler,
    get_haftalik_rutin_takip_sheet,
    hafta_baslangic_str,
    TR_TZ,
)

GITHUB_REPO = "zideofturkey/poke-verimlilik-takibi"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")


def gunluk_verileri_topla():
    ws = get_sheet()
    rows = ws.get_all_records()
    rutinler = get_aktif_rutinler()
    rutin_isimleri = {r["isim"] for r in rutinler}

    bugun = datetime.datetime.now(TR_TZ).date()
    sinir = bugun - datetime.timedelta(days=44)

    gunluk = {}  # tarih_str -> {isim: durum}
    for r in rows:
        try:
            tarih = datetime.datetime.strptime(r["Tarih"], "%Y-%m-%d").date()
        except (ValueError, KeyError):
            continue
        if tarih < sinir or r.get("Görev") not in rutin_isimleri:
            continue
        tarih_str = r["Tarih"]
        gunluk.setdefault(tarih_str, {})[r["Görev"]] = r["Durum"]

    heatmap = []
    for i in range(44, -1, -1):
        d = bugun - datetime.timedelta(days=i)
        d_str = d.strftime("%Y-%m-%d")
        durumlar = gunluk.get(d_str, {})
        rutin_listesi = [
            {"isim": r["isim"], "durum": durumlar.get(r["isim"], "Yapılmadı" if d_str in gunluk else None)}
            for r in rutinler
        ]
        tamamlanan = sum(1 for x in rutin_listesi if x["durum"] in ("Yapıldı", "Telafi"))
        heatmap.append({
            "tarih": d.strftime("%d %B %Y"),
            "tarih_iso": d_str,
            "level": tamamlanan if d_str in gunluk else 0,
            "rutinler": rutin_listesi,
        })
    return heatmap


def _hafta_baslangiclari_uret(kac_hafta):
    """Bugünün haftasından geriye doğru `kac_hafta` adet Pazartesi
    tarihini (YYYY-MM-DD) eskiden-yeniye sıralı döndürür. hafta_baslangic_str()
    ile AYNI mantığı (o an neyse 'bugünkü hafta') kullanır, sadece
    geriye dönük - böylece HaftalikRutinTakip'teki HaftaBaslangic
    değerleriyle birebir eşleşir."""
    bugun = datetime.datetime.now(TR_TZ).date()
    bu_hafta_pazartesi = bugun - datetime.timedelta(days=bugun.weekday())
    return [
        (bu_hafta_pazartesi - datetime.timedelta(weeks=i)).strftime("%Y-%m-%d")
        for i in range(kac_hafta - 1, -1, -1)
    ]


def _hafta_etiketi(hafta_baslangic_str_deger):
    """'2026-07-28' -> '28 Tem - 3 Ağu' gibi okunabilir bir aralık etiketi."""
    try:
        baslangic = datetime.datetime.strptime(hafta_baslangic_str_deger, "%Y-%m-%d").date()
    except ValueError:
        return hafta_baslangic_str_deger
    bitis = baslangic + datetime.timedelta(days=6)
    aylar = ["Oca", "Şub", "Mar", "Nis", "May", "Haz", "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"]
    if baslangic.month == bitis.month:
        return f"{baslangic.day} - {bitis.day} {aylar[bitis.month - 1]}"
    return f"{baslangic.day} {aylar[baslangic.month - 1]} - {bitis.day} {aylar[bitis.month - 1]}"


def haftalik_rutin_heatmap_topla(kac_hafta=12):
    """Günlük ısı haritasının (gunluk_verileri_topla) haftalık eksendeki
    eşleniği. HaftalikRutinTakip sekmesindeki satırları HaftaBaslangic'e
    göre gruplar.

    ÖNEMLİ TASARIM KARARI - rutin sayısı zamanla değişebilir: ilk
    haftalarda tek bir haftalık rutin (ör. sadece 'Oda tozu alma') vardı,
    sonradan yeni rutinler eklendi. Her haftanın 'level'ı (ve dolayısıyla
    heatmap rengi) o haftaya AİT olan rutin sayısına göre hesaplanmalı -
    şu an aktif olan (güncel) rutin sayısına göre DEĞİL. Aksi halde eski,
    az-rutinli bir hafta (1/1 tamamlanmış) ile yeni, çok-rutinli bir
    hafta (2/4 tamamlanmış) aynı ölçekte karşılaştırılıp yanıltıcı bir
    görsel ortaya çıkar. Çözüm: rutin listesi şu anki aktif listeden
    DEĞİL, o haftaya ait gerçek HaftalikRutinTakip satırlarından
    türetiliyor - her hafta kendi gerçek payyasına göre orantılanıyor,
    rutin sayısı ileride artsa/azalsa da otomatik ayak uyduruyor.

    Günlük tarafla FARK: 'Telafi' durumu haftalık rutinlerde kavramsal
    olarak yok (günün önemi olmadığı için telafi kavramı burada
    anlamsız) - bu yüzden telafi noktası mantığı haftalık modda hiç
    uygulanmaz, sadece dolgu rengi kullanılır."""
    ws = get_haftalik_rutin_takip_sheet()
    rows = ws.get_all_records()

    hafta_hafta = {}  # hafta_baslangic -> [{isim, durum}, ...] (o haftanın GERÇEK satırları)
    for r in rows:
        hafta = r.get("HaftaBaslangic")
        isim = r.get("Isim")
        if not hafta or not isim:
            continue
        hafta_hafta.setdefault(hafta, []).append({"isim": isim, "durum": r.get("Durum")})

    hafta_listesi = _hafta_baslangiclari_uret(kac_hafta)
    heatmap = []
    for hafta in hafta_listesi:
        rutin_listesi = hafta_hafta.get(hafta, [])
        hafta_var_mi = hafta in hafta_hafta
        rutin_sayisi_o_hafta = len(rutin_listesi) or 1
        tamamlanan = sum(1 for x in rutin_listesi if x["durum"] == "Yapıldı")
        heatmap.append({
            "tarih": _hafta_etiketi(hafta),
            "tarih_iso": hafta,
            "level": tamamlanan if hafta_var_mi else 0,
            "maks": rutin_sayisi_o_hafta,
            "rutinler": rutin_listesi,
        })
    return heatmap


def haftalik_rutin_oranlari_hesapla(kac_hafta=12):
    """rutin_oranlari_hesapla()'nın haftalık eşleniği - günlük tarafta
    'son 30 gün' neyse, burada 'son kac_hafta hafta' o. Not: haftalık
    rutinlerde 'Telafi' durumu yok, sadece Yapıldı/Yapılmadı/Bekliyor -
    bu yüzden oran hesabı sadece 'Yapıldı'yı sayıyor (günlük taraftaki
    gibi Telafi'yi de dahil etmeye gerek yok)."""
    haftalik_rutinler = get_aktif_haftalik_rutinler()
    hafta_seti = set(_hafta_baslangiclari_uret(kac_hafta))

    ws = get_haftalik_rutin_takip_sheet()
    rows = ws.get_all_records()

    sonuc = []
    for rutin in haftalik_rutinler:
        toplam = 0
        yapilan = 0
        for r in rows:
            if r.get("Isim") != rutin["isim"] or r.get("HaftaBaslangic") not in hafta_seti:
                continue
            if r.get("Durum") == "Bekliyor":
                continue  # henüz karara varılmamış hafta - orana dahil etme
            toplam += 1
            if r.get("Durum") == "Yapıldı":
                yapilan += 1
        oran = round((yapilan / toplam) * 100) if toplam else 0
        sonuc.append({"isim": rutin["isim"], "oran": oran})
    return sonuc


def rutin_oranlari_hesapla():
    ws = get_sheet()
    rows = ws.get_all_records()
    rutinler = get_aktif_rutinler()

    bugun = datetime.datetime.now(TR_TZ).date()
    sinir = bugun - datetime.timedelta(days=29)

    sonuc = []
    for rutin in rutinler:
        toplam = 0
        yapilan = 0
        for r in rows:
            if r.get("Görev") != rutin["isim"]:
                continue
            try:
                tarih = datetime.datetime.strptime(r["Tarih"], "%Y-%m-%d").date()
            except (ValueError, KeyError):
                continue
            if tarih < sinir:
                continue
            toplam += 1
            if r["Durum"] in ("Yapıldı", "Telafi"):
                yapilan += 1
        oran = round((yapilan / toplam) * 100) if toplam else 0
        sonuc.append({"isim": rutin["isim"], "oran": oran})
    return sonuc


def gunluk_gorev_gecmisi():
    ws = get_gorevler_sheet()
    rows = ws.get_all_records()
    gruplu = {}
    for r in rows:
        gruplu.setdefault(r["Tarih"], []).append(
            {"metin": r["GorevMetni"], "durum": r["Durum"]}
        )
    sonuc = []
    for tarih in sorted(gruplu.keys(), reverse=True)[:14]:
        d = datetime.datetime.strptime(tarih, "%Y-%m-%d")
        sonuc.append({
            "tarih": d.strftime("%d %B"),
            "gunAdi": ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"][d.weekday()],
            "gorevler": gruplu[tarih],
        })
    return sonuc


def haftalik_hedef_gecmisi():
    ws = get_haftalik_sheet()
    rows = ws.get_all_records()
    gruplu = {}
    for r in rows:
        gruplu.setdefault(r["HaftaBaslangic"], []).append(
            {"hedef": r["HedefMetni"], "durum": r["Durum"]}
        )
    sonuc = []
    for hafta in sorted(gruplu.keys(), reverse=True)[:8]:
        sonuc.append({"hafta": hafta, "hedefler": gruplu[hafta]})
    return sonuc


def workflow_gecmisi():
    if not GITHUB_TOKEN:
        return [], {}
    try:
        resp = requests.get(
            f"https://api.github.com/repos/{GITHUB_REPO}/actions/runs",
            headers={"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github+json"},
            params={"per_page": 40},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"Workflow gecmisi cekilemedi: {e}")
        return [], {}

    def kisa_ad(ham_ad):
        return (ham_ad.replace("Gönder - Proaktif Mesajlar", "Gönder")
                       .replace("Webhook - Anlık Buton İşleme", "Webhook")
                       .replace("Analiz - Haftalık SLM Özeti", "Analiz")
                       .replace("Dinle - Buton Kontrolü", "Dinle")
                       .replace("Temizle - Eski Veri", "Temizle")
                       .replace("Panel - Veri Güncelle", "Panel"))

    sonuc = []
    tur_istatistik = {}  # ad -> {"toplam": n, "basarili": n, "sureler": [sn, ...]}
    for run in data.get("workflow_runs", []):
        ad = kisa_ad(run["name"])
        sure_sn = None
        try:
            baslangic = datetime.datetime.fromisoformat(run["run_started_at"].replace("Z", "+00:00"))
            bitis = datetime.datetime.fromisoformat(run["updated_at"].replace("Z", "+00:00"))
            sure_sn = round((bitis - baslangic).total_seconds())
        except Exception:
            pass

        basarili = run["conclusion"] == "success"
        sonuc.append({
            "ad": ad,
            "zaman": run["created_at"],
            "durum": "ok" if basarili else "warn",
            "runId": str(run["id"]),
            "sureSn": sure_sn,
        })

        if ad not in tur_istatistik:
            tur_istatistik[ad] = {"toplam": 0, "basarili": 0, "sureler": []}
        tur_istatistik[ad]["toplam"] += 1
        if basarili:
            tur_istatistik[ad]["basarili"] += 1
        if sure_sn is not None:
            tur_istatistik[ad]["sureler"].append(sure_sn)

    tur_ozet = []
    for ad, s in tur_istatistik.items():
        ort_sure = round(sum(s["sureler"]) / len(s["sureler"])) if s["sureler"] else None
        tur_ozet.append({
            "ad": ad,
            "toplam": s["toplam"],
            "oran": round((s["basarili"] / s["toplam"]) * 100) if s["toplam"] else 0,
            "ortSureSn": ort_sure,
        })

    return sonuc[:15], tur_ozet


def koc_kararlari():
    ws = get_sheet()
    rows = ws.get_all_records()
    sonuc = []
    for r in rows:
        if str(r.get("Görev", "")).startswith("Koç kararı:"):
            sonuc.append({
                "rutin": r["Görev"].replace("Koç kararı: ", ""),
                "tarih": r["Tarih"],
                "sonuc": r["Durum"],
            })
    return sonuc[-10:]


def slm_karar_gecmisi():
    from common import get_slm_log_sheet
    try:
        ws = get_slm_log_sheet()
        rows = ws.get_all_records()
    except Exception as e:
        print(f"SLM log okunamadi: {e}")
        return [], []
    sonuc = []
    for r in rows[-20:]:
        sonuc.append({
            "tarih": r.get("Tarih", ""),
            "saat": r.get("Saat", ""),
            "kategori": r.get("Kategori", ""),
            "ozet": r.get("MesajOzet", ""),
            "detay": r.get("Detay", ""),
        })

    dagilim = {}
    for r in rows:
        k = r.get("Kategori", "Bilinmiyor")
        dagilim[k] = dagilim.get(k, 0) + 1
    dagilim_listesi = sorted(
        [{"kategori": k, "sayi": v} for k, v in dagilim.items()],
        key=lambda x: x["sayi"], reverse=True,
    )

    return list(reversed(sonuc)), dagilim_listesi


def hata_gecmisi():
    try:
        from common import get_sheet
        spreadsheet = get_sheet().spreadsheet
        ws = spreadsheet.worksheet("HataLog")
        rows = ws.get_all_records()
    except Exception as e:
        print(f"HataLog okunamadi (henuz olusmamis olabilir): {e}")
        return []
    sonuc = [{"tarih": r.get("Tarih", ""), "saat": r.get("Saat", ""), "baglam": r.get("Baglam", "")} for r in rows]
    return list(reversed(sonuc))[:15]


def main():
    heatmap = gunluk_verileri_topla()
    rutin_oranlari = rutin_oranlari_hesapla()
    haftalik_rutin_heatmap = haftalik_rutin_heatmap_topla()
    haftalik_rutin_oranlari = haftalik_rutin_oranlari_hesapla()

    son_7_gun_tamamlanan = sum(g["level"] for g in heatmap[-7:])
    son_7_gun_toplam = len(get_aktif_rutinler()) * 7
    hafta_yuzdesi = round((son_7_gun_tamamlanan / son_7_gun_toplam) * 100) if son_7_gun_toplam else 0

    workflow_liste, workflow_tur_ozet = workflow_gecmisi()
    slm_liste, slm_dagilim = slm_karar_gecmisi()

    veri = {
        "uretim_zamani": datetime.datetime.now(TR_TZ).isoformat(),
        "heroStats": {
            "haftaTamamlamaYuzdesi": hafta_yuzdesi,
        },
        "heatmap": heatmap,
        "rutinOranlari": rutin_oranlari,
        "haftalikRutinHeatmap": haftalik_rutin_heatmap,
        "haftalikRutinOranlari": haftalik_rutin_oranlari,
        "gunlukGorevGecmisi": gunluk_gorev_gecmisi(),
        "haftalikHedefGecmisi": haftalik_hedef_gecmisi(),
        "workflowGecmisi": workflow_liste,
        "workflowTurOzet": workflow_tur_ozet,
        "kocKararlari": koc_kararlari(),
        "slmKararlari": slm_liste,
        "slmDagilim": slm_dagilim,
        "hataGecmisi": hata_gecmisi(),
    }

    with open("panel/data.json", "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=2)
    print("panel/data.json yazıldı.")


if __name__ == "__main__":
    main()
