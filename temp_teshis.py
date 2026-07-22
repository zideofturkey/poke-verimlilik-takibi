"""GEÇİCİ TEŞHİS SCRIPTİ - iş bitince silinecek.
GunlukGorevler ve SLMLog sekmelerinin son satırlarını okuyup çıktı verir.
"""
from common import get_gorevler_sheet, get_sheet

def main():
    print("=== GunlukGorevler (son 15 satır) ===")
    ws = get_gorevler_sheet()
    rows = ws.get_all_values()
    header = rows[0] if rows else []
    print("HEADER:", header)
    for r in rows[-15:]:
        print(r)

    print("\n=== SLMLog (son 15 satır) ===")
    spreadsheet = get_sheet()
    try:
        slm_ws = spreadsheet.worksheet("SLMLog")
        slm_rows = slm_ws.get_all_values()
        print("HEADER:", slm_rows[0] if slm_rows else [])
        for r in slm_rows[-15:]:
            print(r)
    except Exception as e:
        print("SLMLog okunamadı:", e)

if __name__ == "__main__":
    main()
