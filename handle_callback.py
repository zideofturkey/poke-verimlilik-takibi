"""
GitHub Actions'ın repository_dispatch (telegram_callback) event'i ile
ANINDA tetiklenir. getUpdates ile beklemek yerine, Cloudflare Worker'ın
webhook üzerinden ilettiği güncellemeyi doğrudan işler.
"""

import json
import os
from common import send_message, answer_callback, log_to_sheet, save_last_update_id


def process_callback(update):
    if "callback_query" not in update:
        print("callback_query yok, atlanıyor.")
        return

    cq = update["callback_query"]
    callback_data = cq["data"]
    print(f"[webhook] Buton basıldı: {callback_data}")

    answer_callback(cq["id"])

    # Aynı update_id'yi polling tarafı (dinle.py) tekrar işlemesin diye
    # offset dosyasını da ilerletiyoruz.
    if "update_id" in update:
        save_last_update_id(update["update_id"])

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


def main():
    payload_raw = os.environ["CLIENT_PAYLOAD"]
    payload = json.loads(payload_raw)
    update = payload["update"]
    process_callback(update)


if __name__ == "__main__":
    main()
