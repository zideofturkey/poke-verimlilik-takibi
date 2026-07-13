from common import get_bekleyen_soru
deger = get_bekleyen_soru()
with open("teshis_sonucu.txt", "w") as f:
    f.write(f"bekleyen_soru = '{deger}'\n")
print(f"Yazildi: '{deger}'")
