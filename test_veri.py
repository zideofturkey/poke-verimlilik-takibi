"""
Tek seferlik yardımcı: SLM analizini test etmek için sentetik veri
ekler/siler. Eklenen satırlar "TEST_VERI" etiketiyle işaretlenir, böylece
gerçek geçmiş kayıtla karışmadan geri temizlenebilir.

Kullanım:
    python test_veri.py ekle
    python test_veri.py sil
"""

import sys
import datetime
from common import get_sheet, TR_TZ

ETIKET = "TEST_VERI"

SENTETIK = [
    # (gun_farki, gorev, durum)
    (1, "Fransızca çalışma", "Yapıldı"),
    (1, "Sabah telefon rutini", "Yapıldı"),
    (1, "Akşam telefon rutini", "Yapılmadı"),
    (1, "Verimli video izleme", "Yapıldı"),
    (2, "Fransızca çalışma", "Yapılmadı"),
    (2, "Sabah telefon rutini", "Yapıldı"),
    (2, "Akşam telefon rutini", "Yapılmadı"),
    (2, "Verimli video izleme", "Yapıldı"),
    (3, "Fransızca çalışma", "Yapıldı"),
    (3, "Sabah telefon rutini", "Yapılmadı"),
    (3, "Akşam telefon rutini", "Yapılmadı"),
    (3, "Verimli video izleme", "Yapıldı"),
    (4, "Fransızca çalışma", "Yapıldı"),
    (4, "Sabah telefon rutini", "Yapıldı"),
]


def ekle():
    ws = get_sheet()
    bugun = datetime.datetime.now(TR_TZ).date()
    for gun_farki, gorev, durum in SENTETIK:
        tarih = (bugun - datetime.timedelta(days=gun_farki)).strftime("%Y-%m-%d")
        ws.append_row([tarih, "12:00", gorev, durum, ETIKET])
    print(f"{len(SENTETIK)} sentetik satır eklendi.")


def sil():
    ws = get_sheet()
    rows = ws.get_all_values()
    silinecek = [i + 1 for i, row in enumerate(rows) if len(row) >= 5 and row[4] == ETIKET]
    for satir_no in reversed(silinecek):
        ws.delete_rows(satir_no)
    print(f"{len(silinecek)} sentetik satır silindi.")


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ("ekle", "sil"):
        print("Kullanım: python test_veri.py [ekle|sil]")
        sys.exit(1)
    {"ekle": ekle, "sil": sil}[sys.argv[1]]()
