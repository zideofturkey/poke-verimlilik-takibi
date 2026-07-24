"""GEÇİCİ KONTROL+TEMİZLİK - kullanıcının gerçek mesajından ("kalan
günlük görevlerim neler") kaynaklanan hatalı kaydı bulur ve siler."""
import datetime
from common import get_gorevler_sheet, TR_TZ

def main():
    bugun = datetime.datetime.now(TR_TZ).strftime("%Y-%m-%d")
    ws = get_gorevler_sheet()
    rows = ws.get_all_values()
    print(f"=== Bugün ({bugun}) GunlukGorevler ===")
    for i, r in enumerate(rows):
        if i == 0 or (r and r[0] == bugun):
            print(i + 1, r)

    for i, r in enumerate(rows):
        if r and r[0] == bugun and len(r) >= 3 and "kalan günlük görevlerim neler" in r[2]:
            ws.delete_rows(i + 1)
            print(f"\nHatalı kayıt silindi: satır {i+1} -> {r}")

if __name__ == "__main__":
    main()
