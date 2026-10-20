"""Kur belirsizliği yöntemlerinin ECB kurlarıyla geçmişe dönük sınaması (docs/HATA_AZALTMA_ANALIZI.md, bölüm 7).

Her tahmin günü için yalnızca o güne kadarki kurlardan h günlük kur oranının %10 ve %90 uçları kurulur; gerçekleşen
oranın alt uçtan düşük (dövizli alacak için kötümser) ve üst uçtan yüksek (dövizli borç için kötümser) çıkma sıklığı
sayılır. Hedef her iki uçta %10. Tahmin günleri h gün arayla (örtüşmeyen pencereler), 2010'dan itibaren; sonuçlar
bütün dönem ve iki yarı (2010-2017, 2018-2026) için. Kıyas: kur sabit (TL karşılığı bugünkü kurla).

Veri: ECB euro referans kurları (tools/ecb_kurlari.py). Kullanım: python tools/kur_sinamasi.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

DATA = Path(__file__).resolve().parents[1] / "src" / "radar" / "data" / "ecb_try_kurlari.csv"
VARIANTS = {"sürüklenmesiz, bütün geçmiş": (True, None), "sürüklenmeli, bütün geçmiş": (False, None),
            "sürüklenmeli, son 3 yıl": (False, 3 * 365), "sürüklenmeli, son 1 yıl": (False, 365)}
PERIODS = (("2010-01-01", "2026-12-31"), ("2010-01-01", "2017-12-31"), ("2018-01-01", "2026-12-31"))


def band(hist: pd.Series, h: int, demean: bool, window: int | None) -> tuple[float, float]:
    if window:
        hist = hist.iloc[-window:]
    r = (hist.shift(-h) - hist).dropna().to_numpy()
    if demean:
        r = r - r.mean()
    lo, hi = np.quantile(r, [0.10, 0.90])
    return float(np.exp(lo)), float(np.exp(hi))


def main() -> None:
    log = np.log(pd.read_csv(DATA, parse_dates=["date"]).set_index("date")[["EUR", "USD"]].asfreq("D").ffill())
    print("| Döviz | Ufuk | Dönem | n | Kur sabit: düşük çıkma | " + " | ".join(f"{k} (alt / üst)" for k in VARIANTS) + " |")
    print("|" + "---|" * (5 + len(VARIANTS)))
    for cur in ("USD", "EUR"):
        for h in (30, 60, 90):
            for a, b in PERIODS:
                days = pd.date_range(a, min(pd.Timestamp(b), log.index[-1] - pd.Timedelta(days=h)), freq=f"{h}D")
                count = {k: [0, 0] for k in VARIANTS}
                below_const = 0
                for d in days:
                    past = log.loc[:d, cur]
                    real = float(np.exp(log.loc[d + pd.Timedelta(days=h), cur] - log.loc[d, cur]))
                    below_const += real < 1
                    for k, (dm, w) in VARIANTS.items():
                        lo, hi = band(past, h, dm, w)
                        count[k][0] += real < lo
                        count[k][1] += real > hi
                n = len(days)
                cells = " | ".join(f"%{x / n * 100:.1f} / %{y / n * 100:.1f}" for x, y in count.values())
                print(f"| {cur} | {h} | {a[:4]}-{b[:4]} | {n} | %{below_const / n * 100:.0f} | {cells} |")


if __name__ == "__main__":
    main()
