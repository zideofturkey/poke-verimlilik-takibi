"""GEÇİCİ TEST HAZIRLIĞI - 20 Temmuz görevini tekrar 'Süresi Doldu' yapar."""
from common import get_gorevler_sheet

def main():
    ws = get_gorevler_sheet()
    rows = ws.get_all_values()
    for i, r in enumerate(rows):
        if (r and r[0] == "2026-07-20" and len(r) >= 4
                and r[2] == "Claude token limitlerini aşma problemi videosunu gemini ile izleyip not çıkarma"):
            ws.update_cell(i + 1, 4, "Süresi Doldu")
            print(f"Test için 'Süresi Doldu'ya geri alındı: satır {i+1}")
            return
    print("Görev bulunamadı!")

if __name__ == "__main__":
    main()
