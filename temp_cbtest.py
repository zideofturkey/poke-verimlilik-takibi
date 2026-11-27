import os, sys
os.environ.setdefault("CLIENT_PAYLOAD", "{}")
import common, handle_update as h

gonderilen = []
common.requests.post = lambda url, json=None, **k: gonderilen.append(json) or None
h.log_to_sheet = lambda *a, **k: print("   (log_to_sheet atlandı)", a[:2])
h.answer_callback = lambda *a: None
mesajlar = []
orijinal = common.send_message
def yakala(text, buttons=None):
    mesajlar.append(text)
    orijinal(text, buttons)
h.send_message = yakala

# 1) GERÇEK sheet, salt-okunur: süresi dolan sorgusu -> imzalı butonlar
h._sorguyu_cevapla("Süresi doldu olarak işaretlediğin görevleri sorgula")
for p in gonderilen:
    print("MESAJ:", p["text"].replace("\n", " | ")[:250])
    print("BUTON:", [b["callback_data"] for r in p["reply_markup"]["inline_keyboard"] for b in r])
gonderilen.clear()

# 2) GEÇİCİ sekmede kayma testi
ss = common.get_sheet().spreadsheet
tmp = ss.add_worksheet(title="TmpGorev", rows=50, cols=4)
try:
    tmp.update(values=[["Tarih","GorevID","GorevMetni","Durum"],
        ["2026-11-01","","eski görev","Yapıldı"],["2026-11-22","","TESTA","Süresi Doldu"],["2026-11-22","","TESTB","Süresi Doldu"]], range_name="A1")
    common.get_gorevler_sheet = lambda: tmp
    h.get_gorevler_sheet = lambda: tmp
    common.send_message("liste", buttons=[[{"text":"1","callback_data":"gorev_4_evet"},{"text":"2","callback_data":"gorev_4_hayir"}],[{"text":"s","callback_data":"sil_gorev_3"}]])
    bt = [b["callback_data"] for r in gonderilen[-1]["reply_markup"]["inline_keyboard"] for b in r]
    print("imzalı butonlar:", bt)
    tmp.delete_rows(2)   # temizle.py'nin yaptığı: üstten satır silinir, her şey kayar
    print("kaymadan sonra:", tmp.get_all_values())
    h.process_callback({"id": "1", "data": bt[0]})          # TESTB (artık satır 3) -> Yapıldı
    h.process_callback({"id": "1", "data": "gorev_58_evet"}) # eski imzasız, boş satır -> reddedilmeli
    h.process_callback({"id": "1", "data": "sil_gorev_2"})   # imzasız sil -> reddedilmeli
    h.process_callback({"id": "1", "data": bt[2]})          # imzalı sil: TESTA silinmeli
    son = tmp.get_all_values()
    print("SON:", son)
    ok = son == [["Tarih","GorevID","GorevMetni","Durum"],["2026-11-22","","TESTB","Yapıldı"]]
    print("CB_TEST_OK" if ok else "CB_TEST_FAIL")
    print("mesajlar:", [m[:60] for m in mesajlar])
finally:
    ss.del_worksheet(tmp)
    # Silme testi çöp kutusuna yazmış olabilir: test satırını temizle
    ck = common.get_cop_kutusu_sheet()
    vals = ck.get_all_values()
    for i in range(len(vals), 1, -1):
        if "TEST" in " ".join(vals[i-1]):
            ck.delete_rows(i)
            print("CopKutusu test satırı silindi:", i)
