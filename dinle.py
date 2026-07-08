"""
GitHub Actions tarafından her birkaç dakikada bir çalıştırılır.
Tek seferlik bir kontrol yapar: yeni buton basılmış mı diye bakar,
varsa işler, kaydeder ve kapanır (sonsuz döngü YOK - Actions'a uygun).
"""

import requests
from common import (
    BASE_URL,
    load_last_update_id,
    save_last_update_id,
    send_message,
    answer_callback,
    log_to_sheet,
)


def process_update(update):
    if "callback_query" not in update:
        return

    cq = update["callback_query"]
    callback_data = cq["data"]
    print(f"Buton basıldı: {callback_data}")
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


def main():
    last_update_id = load_last_update_id()

    params = {"timeout": 0}
    if last_update_id is not None:
        params["offset"] = last_update_id + 1

    resp = requests.get(f"{BASE_URL}/getUpdates", params=params, timeout=15)
    data = resp.json()

    updates = data.get("result", [])
    if not updates:
        print("Yeni güncelleme yok.")
        return

    for update in updates:
        last_update_id = update["update_id"]
        save_last_update_id(last_update_id)
        process_update(update)


if __name__ == "__main__":
    main()
