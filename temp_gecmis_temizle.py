"""GEÇİCİ TEMİZLİK - sahte kaydı siler, asıl 20 Temmuz görevini elle
doğru şekilde 'Yapıldı' işaretler (fonksiyonun kendisini de böylece
Sheets üzerinde doğrulamış oluyoruz)."""
import datetime
from common import get_gorevler_sheet, TR_TZ

def main():
    ws = get_gorevler_sheet()
    rows = ws.get_all_values()
    bugun = datetime.datetime.now(TR_TZ).strftime("%Y-%m-%d")

    # 1) Bugüne yanlışlıkla eklenen sahte kaydı sil
    for i, r in enumerate(rows):
        if (r and r[0] == bugun and len(r) >= 3
                and "Claude token limitlerini aşma problemi" in r[2]):
            ws.delete_rows(i + 1)
            print(f"Sahte kayıt silindi: satır {i+1} -> {r}")
            break

    # 2) Asıl 20 Temmuz görevini doğru şekilde 'Yapıldı' işaretle
    rows = ws.get_all_values()  # güncel hâliyle tekrar oku
    for i, r in enumerate(rows):
        if (r and r[0] == "2026-07-20" and len(r) >= 4
                and r[2] == "Claude token limitlerini aşma problemi videosunu gemini ile izleyip not çıkarma"):
            ws.update_cell(i + 1, 4, "Yapıldı")
            print(f"20 Temmuz görevi 'Yapıldı' olarak işaretlendi: satır {i+1}")
            break

if __name__ == "__main__":
    main()
