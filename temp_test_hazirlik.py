"""GEÇİCİ TEMİZLİK+HAZIRLIK - sahte kaydı siler, 20 Temmuz görevini tekrar
'Süresi Doldu' yapar (yeni düzeltmeyi temiz bir senaryoda test etmek için)."""
import datetime
from common import get_gorevler_sheet, TR_TZ

def main():
    ws = get_gorevler_sheet()
    bugun = datetime.datetime.now(TR_TZ).strftime("%Y-%m-%d")

    rows = ws.get_all_values()
    for i, r in enumerate(rows):
        if (r and r[0] == bugun and len(r) >= 3
                and "Claude token limitlerini aşma problemi" in r[2]):
            ws.delete_rows(i + 1)
            print(f"Sahte kayıt silindi: satır {i+1} -> {r}")
            break

    rows = ws.get_all_values()
    for i, r in enumerate(rows):
        if (r and r[0] == "2026-07-20" and len(r) >= 4
                and r[2] == "Claude token limitlerini aşma problemi videosunu gemini ile izleyip not çıkarma"):
            ws.update_cell(i + 1, 4, "Süresi Doldu")
            print(f"Test için 'Süresi Doldu'ya geri alındı: satır {i+1}")
            break

if __name__ == "__main__":
    main()
