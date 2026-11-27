import os
os.environ.setdefault("CLIENT_PAYLOAD", "{}")
import common

def anomali(ws, ad):
    vals = ws.get_all_values()
    print(f"== {ad}: {len(vals)} satır (grid {ws.row_count}x{ws.col_count})")
    for i, r in enumerate(vals, start=1):
        if i == 1:
            continue
        dolu = [(j, c) for j, c in enumerate(r) if c.strip()]
        if not dolu:
            continue
        if not r[0].strip() or len(r) > 6 or (dolu and dolu[0][0] > 0):
            print(f"  ANOMALİ satır {i}: {r}")
    return vals

g = anomali(common.get_gorevler_sheet(), "GunlukGorevler")
print("  son 8 dolu satır:")
dolu_idx = [i for i, r in enumerate(g, start=1) if any(c.strip() for c in r)]
for i in dolu_idx[-8:]:
    print("   ", i, g[i-1])
anomali(common.get_haftalik_sheet(), "HaftalikHedefler")
anomali(common.get_haftalik_rutin_takip_sheet(), "HaftalikRutinTakip")
t = common.get_sheet().get_all_values()
print(f"== Takip: {len(t)} satır; 'None' içeren:")
for i, r in enumerate(t, start=1):
    if any(c == "None" for c in r):
        print("  ", i, r)
print("  son 6:", t[-6:])
