# -*- coding: utf-8 -*-
"""Poke'un her gün rastgele bir saatte gönderdiği borsa aforizmaları.

Bu liste, gerçek ve doğrulanabilir sözlerden oluşuyor - saygın, başarılı
yatırımcı/borsacıların plan sadakati, sabır, doğru anı bekleme, acele
etmeme ve akıllıca davranma temalı özlü sözleri. Uydurma alıntı riskini
almamak için her söz web araştırmasıyla çapraz kontrol edildi.

ÖNEMLİ: Sözler ORİJİNAL SÖYLENDİĞİ DİLDE tutuluyor (çoğu İngilizce,
çünkü kaynak kişiler İngilizce konuşan yatırımcılar) - Türkçe'ye çevirmek
bazı kavramları (ör. 'sitting', 'the tape', 'blood in the streets' gibi
piyasa jargonunun inceliklerini) kaybettirebiliyordu. Kullanıcının kendi
eklediği sözler ise onun yazdığı dilde (genelde Türkçe) kalıyor - o ayrı
bir Google Sheets sekmesinde (AforizmaKullanici) tutuluyor,
common.py'deki aforizma_sec() ikisini birleştirip seçim yapıyor.
"""

AFORIZMALAR = [
    # --- Jesse Livermore ---
    {"soz": "It never was my thinking that made the big money for me. It always was my sitting.", "yazar": "Jesse Livermore"},
    {"soz": "The big money is not in the buying and selling, but in the waiting.", "yazar": "Jesse Livermore"},
    {"soz": "Patience is essential for trading. When there is nothing to do, do nothing.", "yazar": "Jesse Livermore"},
    {"soz": "Cut your losses short and let your winners run.", "yazar": "Jesse Livermore"},
    {"soz": "I never argue with the tape. To be angry at the market because it unexpectedly goes against you is like getting mad at your lungs because you have pneumonia.", "yazar": "Jesse Livermore"},
    {"soz": "Big movements take time to develop.", "yazar": "Jesse Livermore"},
    {"soz": "Nothing new ever occurs in the business of speculating or investing in securities and commodities.", "yazar": "Jesse Livermore"},
    {"soz": "The game of speculation is the most uniformly fascinating game in the world.", "yazar": "Jesse Livermore"},
    {"soz": "There is nothing new in Wall Street. There can't be because speculation is as old as the hills.", "yazar": "Jesse Livermore"},
    {"soz": "Markets are never wrong, opinions often are.", "yazar": "Jesse Livermore"},
    {"soz": "Wall Street never changes, the pockets change, the suckers change, the stocks change, but Wall Street never changes, because human nature never changes.", "yazar": "Jesse Livermore"},
    {"soz": "Don't take action with a trade until the market, itself, confirms your opinion.", "yazar": "Jesse Livermore"},
    {"soz": "It takes a man a long time to learn all the lessons of all his mistakes.", "yazar": "Jesse Livermore"},
    {"soz": "There is only one side of the market and it is not the bull side or the bear side, but the right side.", "yazar": "Jesse Livermore"},
    {"soz": "A loss never bothers me after I take it. I forget it overnight. But being wrong and not admitting it - that is what does the damage to the pocket book and to the soul.", "yazar": "Jesse Livermore"},

    # --- Warren Buffett ---
    {"soz": "The stock market is a device for transferring money from the impatient to the patient.", "yazar": "Warren Buffett"},
    {"soz": "Be fearful when others are greedy, and greedy when others are fearful.", "yazar": "Warren Buffett"},
    {"soz": "If you cannot control your emotions, you cannot control your money.", "yazar": "Warren Buffett"},
    {"soz": "Diversification is protection against ignorance.", "yazar": "Warren Buffett"},
    {"soz": "Our favorite holding period is forever.", "yazar": "Warren Buffett"},
    {"soz": "It's far better to buy a wonderful company at a fair price than a fair company at a wonderful price.", "yazar": "Warren Buffett"},
    {"soz": "Risk comes from not knowing what you are doing.", "yazar": "Warren Buffett"},
    {"soz": "Someone's sitting in the shade today because someone planted a tree a long time ago.", "yazar": "Warren Buffett"},
    {"soz": "The most important quality for an investor is temperament, not intellect.", "yazar": "Warren Buffett"},
    {"soz": "Price is what you pay. Value is what you get.", "yazar": "Warren Buffett"},
    {"soz": "It's only when the tide goes out that you learn who has been swimming naked.", "yazar": "Warren Buffett"},

    # --- Charlie Munger ---
    {"soz": "The big money is not in the buying and the selling, but in the waiting.", "yazar": "Charlie Munger"},
    {"soz": "The first rule of compounding: never interrupt it unnecessarily.", "yazar": "Charlie Munger"},
    {"soz": "It is not a bad idea to review one's stupidities regularly.", "yazar": "Charlie Munger"},

    # --- Paul Tudor Jones ---
    {"soz": "The most important rule of trading is to play great defense, not great offense.", "yazar": "Paul Tudor Jones"},
    {"soz": "Don't focus on making money; focus on protecting what you have.", "yazar": "Paul Tudor Jones"},
    {"soz": "The best trades are the ones in which you have all the factors in your favor. Waiting for such trades requires patience and discipline.", "yazar": "Paul Tudor Jones"},
    {"soz": "You adapt, evolve, compete, or die.", "yazar": "Paul Tudor Jones"},
    {"soz": "Losers average losers.", "yazar": "Paul Tudor Jones"},
    {"soz": "Every day I assume every position I have is wrong.", "yazar": "Paul Tudor Jones"},
    {"soz": "I'm always thinking about losing money as opposed to making money.", "yazar": "Paul Tudor Jones"},
    {"soz": "Never play macho man with the market.", "yazar": "Paul Tudor Jones"},

    # --- Ed Seykota ---
    {"soz": "The elements of good trading are: cutting losses, cutting losses, and cutting losses.", "yazar": "Ed Seykota"},
    {"soz": "The markets are the same now as they were five to ten years ago because they keep changing - just like they did then.", "yazar": "Ed Seykota"},
    {"soz": "Win or lose, everybody gets what they want out of the market. Some people seem to like to lose, so they win by losing money.", "yazar": "Ed Seykota"},

    # --- Mark Douglas ---
    {"soz": "Anything can happen.", "yazar": "Mark Douglas"},
    {"soz": "If you can learn to create a state of mind that is not affected by the market's behaviour, the struggle will cease to exist.", "yazar": "Mark Douglas"},
    {"soz": "The consistency you seek is in your mind, not in the markets.", "yazar": "Mark Douglas"},
    {"soz": "You create your own game in your mind based on your beliefs, intents, perception and rules.", "yazar": "Mark Douglas"},

    # --- Bruce Kovner ---
    {"soz": "I know where I'm getting out before I get in.", "yazar": "Bruce Kovner"},
    {"soz": "Whenever I enter a position, I have a predetermined stop. That is the only way I can sleep.", "yazar": "Bruce Kovner"},
    {"soz": "In this business you have to be able to entertain conflicting thoughts at the same time.", "yazar": "Bruce Kovner"},

    # --- George Soros ---
    {"soz": "It's not whether you're right or wrong that's important, but how much money you make when you're right and how much you lose when you're wrong.", "yazar": "George Soros"},
    {"soz": "I'm only rich because I know when I'm wrong.", "yazar": "George Soros"},
    {"soz": "Markets are constantly in a state of uncertainty and flux, and money is made by discounting the obvious and betting on the unexpected.", "yazar": "George Soros"},

    # --- Diğer piyasa büyükleri ---
    {"soz": "The key to trading success is emotional discipline. If intelligence were the key, there would be a lot more people making money trading.", "yazar": "Victor Sperandeo"},
    {"soz": "The market does not know you exist. You can do nothing to influence it. You can only control your behavior.", "yazar": "Alexander Elder"},
    {"soz": "Every winner needs to master three essential components of trading: a sound individual psychology, a logical trading system and good money management.", "yazar": "Alexander Elder"},
    {"soz": "I just wait until there is money lying in the corner, and all I have to do is go over there and pick it up. I do nothing in the meantime.", "yazar": "Jim Rogers"},
    {"soz": "One of the best rules anybody can learn about investing is to do nothing, absolutely nothing, unless there is something to do.", "yazar": "Jim Rogers"},
    {"soz": "In investing, what is comfortable is rarely profitable.", "yazar": "Robert Arnott"},
    {"soz": "The four most dangerous words in investing are: 'This time it's different.'", "yazar": "Sir John Templeton"},
    {"soz": "Bull markets are born on pessimism, grow on skepticism, mature on optimism, and die on euphoria.", "yazar": "Sir John Templeton"},
    {"soz": "The intelligent investor is a realist who sells to optimists and buys from pessimists.", "yazar": "Benjamin Graham"},
    {"soz": "The essence of investment management is the management of risks, not the management of returns.", "yazar": "Benjamin Graham"},
    {"soz": "In the short run, the market is a voting machine, but in the long run it is a weighing machine.", "yazar": "Benjamin Graham"},
    {"soz": "In this business, if you're good, you're right six times out of ten. You're never going to be right nine times out of ten.", "yazar": "Peter Lynch"},
    {"soz": "Know what you own, and know why you own it.", "yazar": "Peter Lynch"},
    {"soz": "If most traders would learn to sit on their hands 50 percent of the time, they would make a lot more money.", "yazar": "Bill Lipschutz"},
    {"soz": "The time to buy is when there's blood in the streets.", "yazar": "Baron Rothschild'e atfedilir"},
    {"soz": "He who lives by the crystal ball will eat shattered glass.", "yazar": "Ray Dalio"},
    {"soz": "What is most important isn't knowing the future - it is knowing how to react appropriately to the information available.", "yazar": "Ray Dalio"},
    {"soz": "If you don't bet, you can't win. If you lose all your chips, you can't bet.", "yazar": "Larry Hite"},
    {"soz": "I believe in analysis and not forecasting.", "yazar": "Nicolas Darvas"},
    {"soz": "All a company report and balance sheet can tell you is the past and the present; they cannot tell the future.", "yazar": "Nicolas Darvas"},
    {"soz": "Learn to take losses. The most important thing in making money is not letting your losses get out of hand.", "yazar": "Marty Schwartz"},
    {"soz": "Trading is a psychological game. Most people think they are playing against the market, but the market doesn't care. You're really playing against yourself.", "yazar": "Marty Schwartz"},
    {"soz": "I turned my trading around by finally being willing to lose.", "yazar": "Marty Schwartz"},
    {"soz": "My biggest hurdle to becoming successful was overcoming my ego needs to be right.", "yazar": "Marty Schwartz"},
    {"soz": "The way to build superior long-term returns is through preservation of capital and home runs.", "yazar": "Stanley Druckenmiller"},
    {"soz": "Sometimes the best trade is no trade at all.", "yazar": "Stanley Druckenmiller"},
    {"soz": "I believe that good investors are successful not because of their IQ, but because they have an investing discipline.", "yazar": "Stanley Druckenmiller"},
    {"soz": "The best advice I can give to the novice trader is this: figure out how to make money doing something else, then carry that knowledge over into trading.", "yazar": "Michael Marcus"},
    {"soz": "There are a million ways to make money in the markets. The irony is that they are all very difficult to find.", "yazar": "Jack Schwager"},
    {"soz": "Don't worry about what the markets are going to do, worry about what you are going to do in response to the markets.", "yazar": "Michael Carr"},
    {"soz": "Time is your friend; impulse is your enemy.", "yazar": "John Bogle"},
    {"soz": "The stock market is a giant distraction from the business of investing.", "yazar": "John Bogle"},
    {"soz": "You can't predict. You can prepare.", "yazar": "Howard Marks"},
    {"soz": "The single greatest edge an investor can have is a long-term orientation.", "yazar": "Seth Klarman"},
    {"soz": "The market can stay irrational longer than you can stay solvent.", "yazar": "John Maynard Keynes'e atfedilir"},
    {"soz": "I never bought at the bottom, and I always sold too soon.", "yazar": "Baron Rothschild'e atfedilir"},
    {"soz": "Amateurs think about how much money they can make. Professionals think about how much money they could lose.", "yazar": "Jack Schwager (Market Wizards)"},
    {"soz": "Never invest in a business you cannot understand.", "yazar": "Warren Buffett"},
    {"soz": "Rule No. 1: Never lose money. Rule No. 2: Never forget rule No. 1.", "yazar": "Warren Buffett"},
    {"soz": "You only have to do a very few things right in your life so long as you don't do too many things wrong.", "yazar": "Warren Buffett"},
    {"soz": "Behind every stock is a company. Find out what it's doing.", "yazar": "Peter Lynch"},
    {"soz": "The stock market is never obvious. It is designed to fool most of the people, most of the time.", "yazar": "Jesse Livermore"},
    {"soz": "Spend each day trying to be a little wiser than you were when you woke up.", "yazar": "Charlie Munger"},
    {"soz": "The stock market is filled with individuals who know the price of everything, but the value of nothing.", "yazar": "Philip Fisher"},
    {"soz": "Invest at the point of maximum pessimism.", "yazar": "Sir John Templeton"},
    {"soz": "Mr. Market is there to serve you, not to guide you.", "yazar": "Benjamin Graham"},

    # --- Piyasa özdeyişleri (belirli bir kişiye ait değil, genel bilgelik) ---
    {"soz": "The trend is your friend, until it ends.", "yazar": "Piyasa özdeyişi"},
    {"soz": "Plan your trade, trade your plan.", "yazar": "Piyasa özdeyişi"},
    {"soz": "Bulls make money, bears make money, pigs get slaughtered.", "yazar": "Wall Street özdeyişi"},
    {"soz": "Buy the rumor, sell the news.", "yazar": "Piyasa özdeyişi"},
]
