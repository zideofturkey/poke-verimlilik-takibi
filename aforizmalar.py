# -*- coding: utf-8 -*-
"""Poke'un her gün rastgele bir saatte gönderdiği borsa aforizmaları.

Bu liste, gerçek ve doğrulanabilir sözlerden oluşuyor - saygın, başarılı
yatırımcı/borsacıların plan sadakati, sabır, doğru anı bekleme, acele
etmeme ve akıllıca davranma temalı özlü sözleri. Uydurma alıntı riskini
almamak için her söz web araştırmasıyla çapraz kontrol edildi.

Kullanıcının kendi eklediği sözler burada DEĞİL - onlar ayrı bir Google
Sheets sekmesinde (AforizmaKullanici) tutuluyor, common.py'deki
aforizma_sec() ikisini birleştirip seçim yapıyor.
"""

AFORIZMALAR = [
    {"soz": "Büyük parayı kazandıran şey benim düşüncem değil, sabırla oturmamdı.", "yazar": "Jesse Livermore"},
    {"soz": "Asıl büyük para alım satımda değil, beklemededir.", "yazar": "Jesse Livermore"},
    {"soz": "Sabır borsada olmazsa olmazdır. Yapacak bir şey yoksa, hiçbir şey yapma.", "yazar": "Jesse Livermore"},
    {"soz": "Zararını hemen kes, kazandıranı koşturmaya bırak.", "yazar": "Jesse Livermore"},
    {"soz": "Piyasayla asla tartışma. Beklenmedik şekilde aleyhine döndü diye piyasaya kızman, akciğerlerine kızman kadar anlamsız.", "yazar": "Jesse Livermore"},
    {"soz": "Hatalarından öğren ve onları tekrarlama.", "yazar": "Jesse Livermore"},
    {"soz": "Asla zarardaki pozisyonun üstüne eklemeyerek ortalama düşürme.", "yazar": "Jesse Livermore"},
    {"soz": "Büyük hareketlerin oluşması zaman alır.", "yazar": "Jesse Livermore"},
    {"soz": "Spekülasyon oyununda yeni hiçbir şey olmaz - insan doğası hep aynı kalır.", "yazar": "Jesse Livermore"},
    {"soz": "Borsa, parayı sabırsızdan alıp sabırlıya aktaran bir araçtır.", "yazar": "Warren Buffett"},
    {"soz": "Başkaları açgözlüyken korkulu, başkaları korkuluyken açgözlü ol.", "yazar": "Warren Buffett"},
    {"soz": "Duygularını kontrol edemiyorsan, paranı da kontrol edemezsin.", "yazar": "Warren Buffett"},
    {"soz": "Çeşitlendirme, cehalete karşı bir korumadır.", "yazar": "Warren Buffett"},
    {"soz": "Asıl büyük para alım satımda değil, beklemededir.", "yazar": "Charlie Munger"},
    {"soz": "Ticaretin en önemli kuralı iyi hücum değil, iyi savunma oynamaktır.", "yazar": "Paul Tudor Jones"},
    {"soz": "Para kazanmaya değil, elindekini korumaya odaklan.", "yazar": "Paul Tudor Jones"},
    {"soz": "En iyi işlemler, her faktörün lehine olduğu işlemlerdir - bunları beklemek sabır ve disiplin ister.", "yazar": "Paul Tudor Jones"},
    {"soz": "Kazanmadan önce kaybetmeyi öğrenmen gerekir.", "yazar": "Paul Tudor Jones"},
    {"soz": "Piyasayla asla ego savaşına girme.", "yazar": "Paul Tudor Jones"},
    {"soz": "Asla aşırı işlem yapma.", "yazar": "Paul Tudor Jones"},
    {"soz": "Risk kontrolü, ticarette en önemli şeydir.", "yazar": "Paul Tudor Jones"},
    {"soz": "Pozisyonum aleyhime dönerse hemen çıkarım; lehime dönerse tutmaya devam ederim.", "yazar": "Paul Tudor Jones"},
    {"soz": "İyi ticaretin unsurları şunlardır: zararı kes, zararı kes, zararı kes.", "yazar": "Ed Seykota"},
    {"soz": "Piyasalar beş ya da on yıl öncesiyle aynıdır - çünkü sürekli değişirler.", "yazar": "Ed Seykota"},
    {"soz": "Her şey olabilir.", "yazar": "Mark Douglas"},
    {"soz": "Piyasanın davranışından etkilenmeyen bir zihin hâli yaratmayı öğrenirsen, mücadele sona erer.", "yazar": "Mark Douglas"},
    {"soz": "Aradığın tutarlılık piyasalarda değil, kendi zihnindedir.", "yazar": "Mark Douglas"},
    {"soz": "Bir pozisyona girmeden önce nereden çıkacağımı zaten bilirim.", "yazar": "Bruce Kovner"},
    {"soz": "Bir pozisyona her girdiğimde önceden belirlenmiş bir stop'um vardır - rahat uyuyabilmemin tek yolu bu.", "yazar": "Bruce Kovner"},
    {"soz": "Önemli olan haklı ya da haksız olman değil, haklıyken ne kadar kazandığın, haksızken ne kadar kaybettiğindir.", "yazar": "George Soros"},
    {"soz": "Piyasanın psikolojik faktörlerden ciddi şekilde etkilendiğine inanıyorum.", "yazar": "George Soros"},
    {"soz": "Ticarette başarının anahtarı duygusal disiplindir. Anahtar zeka olsaydı, çok daha fazla kişi para kazanırdı.", "yazar": "Victor Sperandeo"},
    {"soz": "Piyasa senin var olduğunu bilmez. Onu etkileyemezsin, sadece kendi davranışını kontrol edebilirsin.", "yazar": "Alexander Elder"},
    {"soz": "Pek çok yatırımcı duygusal bir tren yolculuğuna çıkar ve kazanmanın asıl şartını kaçırır: duygu yönetimi.", "yazar": "Alexander Elder"},
    {"soz": "Her kazanan üç temel unsuru ustalıkla birleştirmelidir: sağlam bir psikoloji, mantıklı bir sistem, iyi bir para yönetimi.", "yazar": "Alexander Elder"},
    {"soz": "Yatırımla ilgili öğrenilebilecek en iyi kurallardan biri: yapacak bir şey yoksa kesinlikle hiçbir şey yapma.", "yazar": "Jim Rogers"},
    {"soz": "Köşede duran parayı almak için sadece oraya gidip eğilmem gereken anı beklerim.", "yazar": "Jim Rogers"},
    {"soz": "Yatırımda rahat olan şey nadiren kârlıdır.", "yazar": "Robert Arnott"},
    {"soz": "Yatırımdaki en tehlikeli dört kelime: 'Bu sefer farklı.'", "yazar": "Sir John Templeton"},
    {"soz": "Başarılı yatırım, riskten kaçınmak değil riski yönetmektir - sabır en önemli unsurlardan biridir.", "yazar": "Benjamin Graham"},
    {"soz": "Akıllı yatırımcı, iyimserlere satan, kötümserlerden alan bir gerçekçidir.", "yazar": "Benjamin Graham"},
    {"soz": "Bu işte iyiysen, on işlemden altısında haklı çıkarsın - dokuzunda değil.", "yazar": "Peter Lynch"},
    {"soz": "Tüccarlar zamanlarının yarısında ellerini cebinde tutmayı öğrenselerdi, çok daha fazla para kazanırlardı.", "yazar": "Bill Lipschutz"},
    {"soz": "Sokaklarda kan varken almanın tam zamanıdır.", "yazar": "Baron Rothschild'e atfedilir"},
    {"soz": "Kristal küreyle yaşayan, kırık cam yer.", "yazar": "Ray Dalio"},
    {"soz": "Piyasa seni cezalandırmaz - kendi disiplinsizliğin cezalandırır.", "yazar": "Mark Douglas"},
    {"soz": "Plan yap, plana göre işlem yap.", "yazar": "Piyasa özdeyişi"},
    {"soz": "En iyi işlem, bazen hiç işlem yapmamaktır.", "yazar": "Piyasa özdeyişi"},
    {"soz": "Trend dostundur - ona karşı durma.", "yazar": "Piyasa özdeyişi"},
    {"soz": "Domuzlar kesilir, boğalar ve ayılar para kazanır, açgözlüler kaybeder.", "yazar": "Wall Street özdeyişi"},
]
