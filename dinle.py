"""
Yedek mekanizma: webhook başarısız olursa diye GitHub Actions tarafından
saatte bir çalıştırılır. Asıl anlık tepki artık webhook.yml üzerinden geliyor.
"""

import requests
from common import BASE_URL, load_last_update_id, save_last_update_id
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
        if "callback_query" in update:
            process_callback(update["callback_query"])
        elif "message" in update:
            process_message(update["message"])


if __name__ == "__main__":
    main()
