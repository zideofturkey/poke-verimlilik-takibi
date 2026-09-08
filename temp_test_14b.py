import time
import subprocess
from common import _ollama_kur_ve_baslat, _ollama_hazir_mi

print("Ollama kuruluyor/baslatiliyor...")
if not _ollama_hazir_mi():
    _ollama_kur_ve_baslat()

print("14b modeli cekiliyor (bu biraz surebilir)...")
t0 = time.time()
pull = subprocess.run(["ollama", "pull", "qwen2.5:14b"], capture_output=True, text=True, timeout=600)
print(f"Pull suresi: {time.time()-t0:.1f}sn, returncode: {pull.returncode}")
if pull.returncode != 0:
    print("PULL BASARISIZ:", pull.stderr[-1000:])
else:
    print("Pull basarili, simdi test sorgusu gonderiliyor...")
    import requests
    t1 = time.time()
    try:
        resp = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "qwen2.5:14b", "prompt": "Merhaba, bu bir testtir. Sadece 'test basarili' yaz.", "stream": False},
            timeout=120,
        )
        print(f"Sorgu suresi: {time.time()-t1:.1f}sn, status: {resp.status_code}")
        print("Cevap:", resp.json().get("response", "")[:200])
    except Exception as e:
        print("SORGU HATASI:", e)

# Bellek kullanimini da raporla
mem = subprocess.run(["free", "-h"], capture_output=True, text=True)
print("\n--- free -h ---")
print(mem.stdout)
