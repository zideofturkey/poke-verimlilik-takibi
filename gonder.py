"""
GitHub Actions tarafından zamanlanmış olarak çalıştırılır (ör. her sabah 09:00).
Tek seferlik bir görev: proaktif soruyu Telegram'a gönderir ve kapanır.

Kullanım:
    python gonder.py sabah
"""

import sys
from common import send_message

GOREVLER = {
    "sabah": {
        "text": "🌅 Günaydın! Bugün Fransızca çalıştın mı?",
        "buttons": [
            [
                {"text": "Evet", "callback_data": "fransizca_evet"},
                {"text": "Hayır", "callback_data": "fransizca_hayir"},
            ]
        ],
    },
    "hafta_ortasi": {
        "text": "📊 Hafta ortası kontrol: bu hafta hedeflerinin neresindesin?",
        "buttons": [
            [
                {"text": "İyi gidiyorum", "callback_data": "hafta_iyi"},
                {"text": "Geride kaldım", "callback_data": "hafta_geride"},
            ]
        ],
    },
    "pazar": {
        "text": "🗓️ Yeni hafta başlıyor. Bu haftaki hedeflerin neler?",
        "buttons": None,  # bu, serbest metinle cevaplanacak (görev tanımlama)
    },
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in GOREVLER:
        print(f"Kullanım: python gonder.py [{'|'.join(GOREVLER.keys())}]")
        sys.exit(1)

    gorev = GOREVLER[sys.argv[1]]
    send_message(gorev["text"], buttons=gorev["buttons"])
    print(f"Gönderildi: {sys.argv[1]}")


if __name__ == "__main__":
    main()
