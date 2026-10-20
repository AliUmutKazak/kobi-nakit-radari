"""Önceden belirlenen: tarihsel benzetim (alacak: sürüklenmesiz bütün geçmiş; borç: sürüklenmeli son 3 yıl) +
konformal genişletme. Tahmin günü d'de, d'den önce sonucu belli olmuş (d - h'den önceki) ve 2007'den beri h gün
arayla seçilmiş geçmiş tahmin günleri için aynı yöntemle bant kurulur; ilgili ucun ortancaya uzaklığı k ile
çarpıldığında geçmiş aşım oranı <= %10 olacak en küçük k (>= 1) seçilir (split conformal; Vovk ve ark. 2005).
Seçim dönemi 2010-2017; sınav 2018-2026.

Kullanım: python tools/kur_konformal_sinamasi.py [sinav]   (sinav: 2018-2026 de yazdırılır)"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

DATA = Path(__file__).resolve().parents[1] / "src" / "radar" / "data" / "ecb_try_kurlari.csv"
fx = pd.read_csv(DATA, parse_dates=["date"]).set_index("date")[["EUR", "USD"]].asfreq("D").ffill()
log = np.log(fx)


def quant(hist: np.ndarray, h: int, side: str):
    if side == "up":
        hist = hist[-3 * 365:]
    r = hist[h:] - hist[:-h]
    if side == "lo":
        r = r - r.mean()
    return np.quantile(r, [0.10, 0.50, 0.90])


def exceed(x, d, h, side, k):
    q10, q50, q90 = quant(x[: d + 1], h, side)
    real = x[d + h] - x[d]
    return real > q50 + k * (q90 - q50) if side == "up" else real < q50 - k * (q50 - q10)


def k_for(x, d, h, side, start):
    past = np.arange(start, d - h + 1, h)                # sonucu d'de belli olan geçmiş tahmin günleri
    if len(past) < 20:
        return 1.0
    for k in np.arange(1.0, 3.01, 0.05):
        if np.mean([exceed(x, p, h, side, k) for p in past]) <= 0.10:
            return k
    return 3.0


for a, b in (("2010-01-01", "2017-12-31"), ("2018-01-01", "2026-12-31")):
    if len(sys.argv) < 2 and a.startswith("2018"):
        print("(sınav dönemi istenmedi)")
        break
    print(f"== {a[:4]}-{b[:4]}")
    for cur in ("USD", "EUR"):
        x = log[cur].to_numpy()
        idx = log.index
        start = int(np.searchsorted(idx, pd.Timestamp("2007-01-01")))
        for h in (30, 60, 90):
            days = np.arange(int(np.searchsorted(idx, pd.Timestamp(a))),
                             min(int(np.searchsorted(idx, pd.Timestamp(b), side="right")), len(x) - h), h)
            out = []
            for side in ("lo", "up"):
                base = np.mean([exceed(x, d, h, side, 1.0) for d in days])
                ks = [k_for(x, d, h, side, start) for d in days]
                conf = np.mean([exceed(x, d, h, side, k) for d, k in zip(days, ks)])
                out.append(f"{side}: önce %{base * 100:.1f} sonra %{conf * 100:.1f} (k ort {np.mean(ks):.2f})")
            print(f"{cur} {h}g n={len(days)} | " + " | ".join(out))
