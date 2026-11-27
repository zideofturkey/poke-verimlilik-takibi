import os, sys
os.environ.setdefault("CLIENT_PAYLOAD", "{}")
import common

ss = common.get_sheet().spreadsheet

# ---- 1) Yeni append'in serseri hücreye dayanıklılığını GEÇİCİ sekmede kanıtla
tmp = ss.add_worksheet(title="TmpAppendTest", rows=100, cols=6)
try:
    tmp.update(values=[["Tarih","GorevID","GorevMetni","Durum"],
                       ["2026-11-01","","a","Yapıldı"],["2026-11-02","","b","Yapıldı"]], range_name="A1")
    tmp.update(values=[["Yapıldı"]], range_name="D20")  # serseri hücre (gerçek olayın aynısı)
    common.guvenli_append_row(tmp, ["2026-11-27", "", "test görevi", "Bekliyor"])
    common.guvenli_append_row(tmp, ["2026-11-27", "", "test görevi 2", "Bekliyor"])
    v = tmp.get_all_values()
    print("TEST sonucu:", v[:6], "| satır20:", v[19] if len(v) > 19 else None)
    ok = v[3] == ["2026-11-27","","test görevi","Bekliyor"] and v[4][2] == "test görevi 2"
finally:
    ss.del_worksheet(tmp)
print("TEST_OK" if ok else "TEST_FAIL")
if not ok:
    sys.exit(1)

# ---- 2) Gerçek onarım
ws = common.get_gorevler_sheet()
v = ws.get_all_values()
def hucre(r, c):
    return v[r-1][c-1] if len(v) >= r and len(v[r-1]) >= c else ""
beklenen_ok = (
    all(hucre(r, 4) == "Yapıldı" and not hucre(r, 1) and not hucre(r, 3) for r in range(58, 62))
    and hucre(62, 6) == "10.00 dersi" or hucre(62, 4) == "2026-11-27"
)
assert hucre(41, 3) == "Kitaplı kahve" and not any(c.strip() for c in v[41]) , "satır 42 boş olmalı"
gorevler = ["10.00 dersi", "SabriAbi görüşme", "DoğruSpot tabela", "Bir filme başlama"]
# kaymış kayıtları doğrula (metinler beklendiği gibi mi)
kayik = [c for r in v[61:66] for c in r if c.strip()]
for g in gorevler:
    assert g in kayik, f"beklenen görev kaymış satırlarda yok: {g}"
ws.batch_clear(["A58:I66"])
for g in gorevler:
    common.guvenli_append_row(ws, ["2026-11-27", "", g, "Bekliyor"])
son = ws.get_all_values()
print("ONARIM sonrası son satırlar:")
for i, r in enumerate(son, start=1):
    if i >= 38 and any(c.strip() for c in r):
        print("  ", i, r[:4], "| fazla:", [c for c in r[4:] if c.strip()])
print("toplam dolu:", sum(1 for r in son if any(c.strip() for c in r)))
