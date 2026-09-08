import sys
sys.path.insert(0, '/home/claude/poke-verimlilik-takibi')
from common import slm_sorgula, get_aktif_rutinler, get_aktif_haftalik_rutinler
from handle_update import BEKLEYEN_ACIKLAMA

def prompt_olustur(text, bekleyen=None):
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

    # handle_update.py'deki tam prompt'u kopyalamak yerine (cok uzun),
    # sadece kategori tanimlarinin OZETINI kullaniyoruz - amac TAM ayni
    # prompt'u tekrar etmek degil, modelin GENEL siniflandirma yetenegini
    # gercek bilinen zor ornekler uzerinde karsilastirmak.
    prompt = (
        "Sen bir verimlilik takip botusun (adın Poke). "
        f"{baglam}\n\n"
        f"Kullanıcı şunu yazdı:\n\"{text}\"\n\n"
        "Bu mesajı asagidaki kategorilerden EN UYGUN olanina ata:\n"
        "- GUNLUK_GOREV: kullanici bugunku/yeni bir GOREV LISTESI yaziyor ya da tek bir gorev EKLIYOR\n"
        "- HAFTALIK_HEDEF: kullanici haftalik hedef ekliyor/yaziyor\n"
        "- SORGULA: kullanici mevcut/gecmis veriyi SORUYOR, ISTIYOR, GORMEK istiyor (yeni bir sey EKLEMIYOR)\n"
        "- GECMIS_GOREV_TAMAMLA: kullanici GECMISTE yazdigi bir gorevi TAMAMLADIGINI bildiriyor\n"
        "- RUTIN_TAMAMLA: kullanici sabit bir rutini (ornek rutinler: " + rutin_isim_listesi + ") tamamladigini soyluyor\n"
        "- BOSA_VAKIT: kullanici bosa vakit gecirdigini anlatiyor\n"
        "- SOHBET: yukaridakilerin hicbirine uymuyor\n\n"
        "SADECE kategori adini yaz, baska hicbir sey yazma. Format:\nKATEGORI: <isim>"
    )
    return prompt

testler = [
    ("Dünden kalan rutin ve görevlerimi sorgula", "SORGULA"),
    ("ulen dünkü görev ve rutinlerimi gönder, işaretlemediklerimi", "SORGULA"),
    ("haftalık görevlerime ekle: \"test hedefi\"", "HAFTALIK_HEDEF"),
    ("\"BaharSpot\" görevini tamamlandı olarak işaretle", "GECMIS_GOREV_TAMAMLA"),
    ("kalan günlük görevlerim neler", "SORGULA"),
    ("geçen haftaki bekleyen statüsündeki görev ve rutinlerimi gönder", "SORGULA"),
]

for model in ["qwen2.5:3b", "qwen2.5:7b", "qwen2.5:14b"]:
    print(f"\n{'='*20} MODEL: {model} {'='*20}")
    for text, beklenen in testler:
        prompt = prompt_olustur(text)
        try:
            sonuc = slm_sorgula(prompt, model=model, zaman_asimi=60)
            dogru = beklenen in sonuc
            durum = "OK" if dogru else "YANLIS"
            print(f"[{durum}] beklenen={beklenen} | cevap={sonuc.strip()[:60]!r} | mesaj={text[:50]!r}")
        except Exception as e:
            print(f"[HATA] {e} | mesaj={text[:50]!r}")
