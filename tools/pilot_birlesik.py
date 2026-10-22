"""Pilotun birincil kararı (protokol 1.8): bütün işletmelerin birleşik analizi.

Girdi: işletme ve ufuk başına bir satır içeren CSV. Sütunlar:
    isletme, ufuk_gun, fark_tahmin, fark_se, m1_tahmin, m1_se   (B2 için isteğe bağlı: kayit, alt_asim, ust_asim)
fark_tahmin ve fark_se o işletmenin pilot puanlamasından (panel "Pilot kayıtları" tablosu ya da
`python -m radar.pilot` çıktısı), m1_tahmin ve m1_se o işletmenin Aşama 0 sonucundan (b1_m1_tahmin, b1_m1_se) alınır.
İşletme başına B1 sonuçları betimleyicidir; karar bu birleşik tablodan verilir.

Kullanım: python tools/pilot_birlesik.py isletmeler.csv
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from radar.pilot import pooled_b1  # noqa: E402

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    firms = pd.read_csv(sys.argv[1])
    out = pooled_b1(firms)
    pd.set_option("display.width", 200)
    print(out.to_string(index=False))
