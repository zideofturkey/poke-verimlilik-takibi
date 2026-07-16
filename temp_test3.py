from common import get_aktif_rutinler, slm_sorgula

def test(text):
    aktif_rutinler = get_aktif_rutinler()
    rutin_isim_listesi = ", ".join(f"'{r['isim']}'" for r in aktif_rutinler)
    baglam = "Şu an kullanıcıya sorduğum, cevap beklediğim bir soru yok."

    prompt = (
        "Sen bir verimlilik takip botusun (adın Poke). "
        f"{baglam}\n\n"
        f"Kullanıcı şunu yazdı:\n\"{text}\"\n\n"
        "Bu mesajı aşağıdaki kategorilerden EN UYGUN olanına ata "
        "(bekleyen soru sadece bir ipucu, mesajın gerçek içeriğine göre "
        "karar ver - biri başka bir konuda yazmış olabilir):\n"
        "- GUNLUK_GOREV: bugün için yapılacaklar listesi veriyor\n"
        "- HAFTALIK_HEDEF: bu haftanın hedeflerini veriyor VEYA mevcut "
        "haftalık hedeflere yeni ekleme yapıyor (ör. 'haftalık hedeflere "
        "ekle: piyano çal' - 'hafta/haftalık' kelimesi + ekleme niyeti "
        "varsa bu kategori, YENI_GOREV DEĞİL)\n"
        "- BOSA_VAKIT: bugün ne kadar boşa vakit geçirdiğini anlatıyor\n"
        "- YENI_GOREV: herhangi bir an kendiliğinden yeni GÜNLÜK (haftalık "
        "DEĞİL) görev/iş ekliyor. 'hafta/haftalık' kelimesi GEÇMİYORSA bu "
        "kategori kullanılır. Kullanıcı genelde eklenecek görev(ler)i tırnak "
        "içinde yazar, "
        "ör: 'bugüne şunu ekliyorum: \"kitap oku\", \"spor yap\"' - birden "
        "fazla görev aynı mesajda olabilir\n"
        f"- RUTIN_TAMAMLA: kullanıcı şu sabit rutinlerden birini tamamladığını "
        f"bildiriyor: {rutin_isim_listesi}. Ör: 'Fransızca rutinimi tamamladım', "
        "'bugün spor yaptım' gibi doğal cümleler. YENI_GOREV ile KARIŞTIRMA - "
        "bu kategori sadece yukarıdaki listedeki rutinler için\n"
        "- SORGULA: kullanıcı bir şeyi EKLEMİYOR, var olan bilgiyi SORUYOR/"
        "İSTİYOR/HATIRLATMAMI istiyor.\n"
        "- SOHBET: yukarıdakilerin hiçbiriyle ilgili değil, genel sohbet/soru\n\n"
        "SADECE şu formatta cevap ver, başka hiçbir şey ekleme:\n"
        "TIP: <KATEGORI>\n"
        "GOREVLER: <SADECE TIP=YENI_GOREV ise: her görevi \" | \" ile "
        "ayırarak yaz (tırnak işaretleri olmadan). Diğer TIP'lerde boş bırak>\n"
        f"RUTIN: <SADECE TIP=RUTIN_TAMAMLA ise: şu listeden BİREBİR aynı "
        f"şekilde yaz, birden fazla rutin tamamlandıysa \" | \" ile ayır: "
        f"{rutin_isim_listesi}. Diğer TIP'lerde boş bırak>\n"
        "CEVAP: <kısa doğal Türkçe yanıt>"
    )
    return slm_sorgula(prompt)

t = "Haftalık hedeflere ek yapacağım. Şu görevleri haftalık hedeflere ekle:\n1. kitap oku\n2. spor yap"
try:
    c = test(t)
    sonuc = f"MESAJ: {t}\nCEVAP:\n{c}"
except Exception as e:
    sonuc = f"HATA: {e}"

with open("test3_sonuc.txt", "w", encoding="utf-8") as f:
    f.write(sonuc)
print("tamamlandi")
