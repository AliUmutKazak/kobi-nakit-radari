"""Dövizli alacak ve borçlarda kur belirsizliği.

Dövizli fatura, kullanıcının girdiği bugünkü kurla TL'ye çevrilir; para geldiği ya da ödendiği gün kur farklıdır.
ECB referans kurlarıyla 2010-2026 sınaması (docs/HATA_AZALTMA_ANALIZI.md, bölüm 7): kur sabit sayılırsa dövizli
alacağın TL karşılığı 30-90 günde dönemlerin %24-36'sında bugünkünden düşük çıktı. Kötümser çizgi bunu hiç
içermiyordu.

Yöntem: tarihsel benzetim. Her senaryo için geçmişten rastgele bir başlangıç günü seçilir ve kurun o günden sonraki
yolu (bugünkü kura oranı) kullanılır; aynı gruptaki dövizler için aynı gün seçilir, böylece dövizler arası ilişki
korunur. Yalnızca tahmin gününe kadarki veri kullanılır. TL'nin ortalama değer kaybı (sürüklenme) ihtiyatlı tarafa
göre ele alınır:
- Alacak ağırlıklı döviz (ufuktaki dövizli alacak, dövizli borçtan fazla): TL'nin değer kaybı geleceğe taşınmaz
  (2005'ten bugüne bütün geçmiş, sürüklenme çıkarılmış; rassal yürüyüş, Meese ve Rogoff 1983, Journal of
  International Economics 14). Kur farkının kasayı büyüteceğine güvenilmez. Sınamada kötümser uç %4-7 aşıldı.
- Borç ağırlıklı döviz: kur yükselişi borcu büyütür; sürüklenme çıkarılırsa senaryoların çoğunda TL değer kazanır ve
  kasa olduğundan dolu görünür. Son 3 yılın kur hareketleri sürüklenmesiyle kullanılır. Sınamada kötümser uç (kurun
  üst ucu) %9-16 aşıldı (hedef %10; dört seçeneğin en iyisi, 2010-2017 ve 2018-2026 yarılarında ayrı ayrı da).

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
SHORT_WINDOW_DAYS = 3 * 365         # borç ağırlıklı dövizde kullanılan son dönem
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


def fx_paths(currencies, as_of, horizon: int, n_sims: int, seed: int, short=()) -> dict[str, np.ndarray]:
    """{döviz: (senaryo, gün) kur oranı}; 0. gün 1. Bilinmeyen döviz ya da yetersiz geçmiş: sözlükte yer almaz.
    short: borç ağırlıklı dövizler (son 3 yıl, sürüklenmeli); diğerleri bütün geçmiş, sürüklenmesiz."""
    h, cur = history(), available(currencies)
    if h is None or not cur:
        return {}
    u = np.random.default_rng(seed + 53).random(n_sims)     # iki grupta da aynı sıra: senaryolar karşılaştırılabilir
    t = np.arange(horizon + 1)
    out = {}
    for group, window, demean in (([c for c in cur if c not in short], None, True),
                                  ([c for c in cur if c in short], SHORT_WINDOW_DAYS, False)):
        if not group:
            continue
        x = np.log(h.loc[:pd.Timestamp(as_of), group].dropna()).to_numpy()   # gruptaki bütün dövizlerin kuru olan günler
        if len(x) < MIN_HISTORY_DAYS + horizon:
            continue
        if window:
            x = x[-window:]
        start = (u * (len(x) - horizon)).astype(int)
        path = x[start[:, None] + t[None, :]] - x[start][:, None, :]
        if demean:
            mu = np.diff(x, axis=0).mean(axis=0)                           # günlük ortalama log değişim
            path = path - mu[None, None, :] * t[None, :, None]
        out |= {c: np.exp(path[:, :, j]) for j, c in enumerate(group)}
    return out
