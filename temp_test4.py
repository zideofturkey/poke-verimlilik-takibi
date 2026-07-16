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
        "- GUNLUK_GOREV: bugün için yapılacaklar listesi veriyor. ÖNEMLİ: "
        "'bugün/bugünkü' kelimesi geçiyorsa ve 'hafta/haftalık' GEÇMİYORSA, "
        "bu KESİNLİKLE GUNLUK_GOREV'dir, HAFTALIK_HEDEF DEĞİLDİR - liste "
        "veriyor olması (madde madde yazması) HAFTALIK_HEDEF sanmana sebep "
        "olmasın\n"
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
        f"bildiriyor: {rutin_isim_listesi}.\n"
        "- SORGULA: kullanıcı bir şeyi EKLEMİYOR, var olan bilgiyi SORUYOR.\n"
        "- SOHBET: yukarıdakilerin hiçbiriyle ilgili değil.\n\n"
        "SADECE şu formatta cevap ver:\n"
        "TIP: <KATEGORI>\n"
        "GOREVLER: <SADECE TIP=YENI_GOREV ise>\n"
        f"RUTIN: <SADECE TIP=RUTIN_TAMAMLA ise>\n"
        "CEVAP: <kısa Türkçe yanıt>"
    )
    return slm_sorgula(prompt)

t = """Bugünkü görevlerim:
1. 13.00 Work out via Scooter
2. 2 video ile Koşullu Milyoner Varsayımları
3. Fitcheck Geliştirmeleri (Claude MCP Denemesi, Frontend'de çok sorun var)
4. The Bear Episode 5
5. Poke Promotion on Chats"""

sonuclar = []
for deneme in range(3):
    try:
        c = test(t)
        sonuclar.append(f"DENEME {deneme+1}:\n{c}")
    except Exception as e:
        sonuclar.append(f"DENEME {deneme+1} HATA: {e}")

with open("test4_sonuc.txt", "w", encoding="utf-8") as f:
    f.write("\n\n====\n\n".join(sonuclar))
print("tamamlandi")
