"""Dövizli alacaklarda kur belirsizliği.

Dövizli fatura, kullanıcının girdiği bugünkü kurla TL'ye çevrilir; para geldiği gün kur farklıdır. ECB referans
kurlarıyla 2010-2026 sınaması (docs/HATA_AZALTMA_ANALIZI.md, madde 9): kur sabit sayılırsa dövizli alacağın TL
karşılığı 30-90 günde dönemlerin %24-36'sında bugünkünden düşük çıktı. Kötümser çizgi bunu hiç içermiyordu.

Yöntem: tarihsel benzetim. Her senaryo için geçmişten rastgele bir başlangıç günü seçilir ve kurun o günden sonraki
yolu (bugünkü kura oranı) kullanılır; bütün dövizler için aynı gün seçilir, böylece dövizler arası ilişki korunur.
Sürüklenme çıkarılır: TL'nin geçmişteki ortalama değer kaybı geleceğe taşınmaz (rassal yürüyüş; Meese ve Rogoff
1983, Journal of International Economics 14). Kur farkının kasayı büyüteceğine güvenilmez. Yalnızca tahmin gününe
kadarki veri kullanılır.

Kaynak: Avrupa Merkez Bankası (ECB) euro referans kurları; EUR dışındaki dövizler çapraz kurdan türetilmiştir
(tools/ecb_kurlari.py). Bu veriler ECB internet sitesinden ücretsiz edinilebilir. ECB kurları yalnızca bilgi
amaçlıdır; burada dönüşüm için değil, yalnızca geçmiş dalgalanmayı ölçmek için kullanılır.
"""
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

DATA = Path(__file__).with_name("data") / "ecb_try_kurlari.csv"
MIN_HISTORY_DAYS = 2 * 365          # en az iki yıllık geçmiş yoksa kur belirsizliği eklenmez
SOURCE = ("Kur belirsizliği: Avrupa Merkez Bankası (ECB) euro referans kurları, 2005'ten bugüne; EUR dışındaki "
          "dövizler çapraz kurdan türetildi. Veriler ECB internet sitesinden ücretsiz edinilebilir.")


@lru_cache(maxsize=1)
def history() -> pd.DataFrame | None:
    if not DATA.exists():
        return None
    df = pd.read_csv(DATA, parse_dates=["date"]).set_index("date").sort_index()
    return df.asfreq("D").ffill()       # hafta sonu ve tatil: bir önceki iş gününün kuru


def available(currencies) -> list[str]:
    h = history()
    return [] if h is None else [c for c in currencies if c in h.columns]


def fx_paths(currencies, as_of, horizon: int, n_sims: int, seed: int) -> dict[str, np.ndarray]:
    """{döviz: (senaryo, gün) kur oranı}; 0. gün 1. Bilinmeyen döviz ya da yetersiz geçmiş: sözlükte yer almaz."""
    h, cur = history(), available(currencies)
    if h is None or not cur:
        return {}
    x = np.log(h.loc[:pd.Timestamp(as_of), cur].dropna()).to_numpy()     # bütün dövizlerin kuru olan günler
    if len(x) < MIN_HISTORY_DAYS + horizon:
        return {}
    start = np.random.default_rng(seed + 53).integers(0, len(x) - horizon, n_sims)
    t = np.arange(horizon + 1)
    mu = np.diff(x, axis=0).mean(axis=0)                                  # günlük ortalama log değişim (sürüklenme)
    path = x[start[:, None] + t[None, :]] - x[start][:, None, :] - mu[None, None, :] * t[None, :, None]
    return {c: np.exp(path[:, :, j]) for j, c in enumerate(cur)}
