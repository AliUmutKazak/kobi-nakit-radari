"""Önceden belirlenen yöntem: tarihsel benzetim, genişleyen pencere (2005'ten tahmin gününe kadar), sürüklenme
çıkarılmış (rassal yürüyüş; Meese-Rogoff 1983). Kıyas: kur sabit. Örtüşmeyen pencereler (h gün arayla tahmin günleri),
2010'dan itibaren. Veri: ECB euro referans kurları (tools/ecb_kurlari.py). Ölçüt: gerçekleşen kur oranının %10 alt ve %90 üst uçların dışına düşme sıklığı + Kupiec."""
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

DATA = Path(__file__).resolve().parents[1] / "src" / "radar" / "data" / "ecb_try_kurlari.csv"
fx = pd.read_csv(DATA, parse_dates=["date"]).set_index("date")[["EUR", "USD"]].asfreq("D").ffill()
log = np.log(fx)


def kupiec(x, n, p):
    if n == 0:
        return np.nan
    ll0 = x * np.log(p) + (n - x) * np.log(1 - p)
    ph = x / n
    ll1 = (x * np.log(ph) if x else 0) + ((n - x) * np.log(1 - ph) if x < n else 0)
    return 1 - stats.chi2.cdf(-2 * (ll0 - ll1), 1)


def band(hist_log, h, demean=True, window=None):
    if window:
        hist_log = hist_log.iloc[-window:]
    r = (hist_log.shift(-h) - hist_log).dropna().to_numpy()
    if demean:
        r = r - r.mean()
    return np.exp(np.quantile(r, [0.10, 0.90]))


for cur in ("USD", "EUR"):
    for h in (30, 60, 90):
        days = pd.date_range("2010-01-01", fx.index[-1] - pd.Timedelta(days=h), freq=f"{h}D")
        rows = []
        for d in days:
            past = log.loc[:d, cur]
            real = float(np.exp(log.loc[d + pd.Timedelta(days=h), cur] - log.loc[d, cur]))
            lo, hi = band(past, h)
            lo3, hi3 = band(past, h, window=3 * 365)
            rows.append((real, lo, hi, lo3, hi3))
        r = pd.DataFrame(rows, columns=["real", "lo", "hi", "lo3", "hi3"])
        n = len(r)
        const_lo, const_hi = int((r.real < 1).sum()), int((r.real > 1).sum())
        hs_lo, hs_hi = int((r.real < r.lo).sum()), int((r.real > r.hi).sum())
        h3_lo, h3_hi = int((r.real < r.lo3).sum()), int((r.real > r.hi3).sum())
        print(f"{cur} h{h} n={n} | sabit kur: alt %{const_lo / n * 100:.0f} | "
              f"tarihsel (genişleyen): alt %{hs_lo / n * 100:.1f} (p {kupiec(hs_lo, n, .1):.2f}) üst %{hs_hi / n * 100:.1f} "
              f"(p {kupiec(hs_hi, n, .1):.2f}) q10 ort {r.lo.mean():.3f} | son 3 yıl penceresi: alt %{h3_lo / n * 100:.1f} üst %{h3_hi / n * 100:.1f}")
