"""
Yedek mekanizma: webhook başarısız olursa diye GitHub Actions tarafından
saatte bir çalıştırılır. Asıl anlık tepki artık webhook.yml üzerinden geliyor.
"""

import requests
from common import (
    BASE_URL, load_last_update_id, save_last_update_id,
    update_zaten_islendi_mi, update_islendi_isaretle, hata_logla, send_message,
)
from handle_update import process_callback, process_message


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
        save_last_update_id(update["update_id"])
        if update_zaten_islendi_mi(update["update_id"]):
            print(f"Update {update['update_id']} zaten işlenmiş (muhtemelen webhook ile çakıştı), atlanıyor.")
            continue

        try:
            if "callback_query" in update:
                process_callback(update["callback_query"])
            elif "message" in update:
                process_message(update["message"])
        except Exception as e:
            # GÜVENLİK AĞI: webhook'un kaçırdığı bir mesajı yakalamak
            # dinle.py'nin TEK işi - burada da çökerse kullanıcı asla
            # sessiz kalmamalı.
            import traceback
            hata_logla("dinle.main (beklenmedik çökme)", traceback.format_exc())
            try:
                send_message("Şu an bunu işleyemedim (teknik bir sorun oldu) — tekrar dener misin?")
            except Exception:
                pass
            print(f"BEKLENMEDİK HATA: {e}")
            continue  # işlendi olarak İŞARETLEME - bir sonraki saatte tekrar denensin

        update_islendi_isaretle(update["update_id"])


if __name__ == "__main__":
    main()
