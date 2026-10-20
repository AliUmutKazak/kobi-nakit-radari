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
Son adımda konformal genişletme (conformal_k): geçmişte uçlar %10'dan sık aşıldıysa bant o kadar açılır. Sınav
dönemi 2018-2026'da borç tarafı aşımı %12,1'den %9,5'e indi.

Kaynak: Avrupa Merkez Bankası (ECB) euro referans kurları; EUR dışındaki dövizler çapraz kurdan türetilmiştir
(tools/ecb_kurlari.py). Bu veriler ECB internet sitesinden ücretsiz edinilebilir. ECB kurları yalnızca bilgi
amaçlıdır; burada dönüşüm için değil, yalnızca geçmiş dalgalanmayı ölçmek için kullanılır.
"""
import io
import os
import zipfile
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

DATA = Path(__file__).with_name("data") / "ecb_try_kurlari.csv"         # pakette gelen tablo
ECB_URL = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.zip"  # yalnızca bu adres; kullanıcı verisi gitmez
CURRENCIES = ("USD", "GBP", "CHF", "CNY")                                # EUR dışında tabloya girenler (çapraz kur)
MAX_DOWNLOAD = 5_000_000                                                 # zip ~0,7 MB; fazlası reddedilir
MAX_CSV = 30_000_000
MIN_HISTORY_DAYS = 2 * 365          # en az iki yıllık geçmiş yoksa kur belirsizliği eklenmez
SHORT_WINDOW_DAYS = 3 * 365         # borç ağırlıklı dövizde kullanılan son dönem
SOURCE = ("Kur belirsizliği: Avrupa Merkez Bankası (ECB) euro referans kurları, 2005'ten bugüne; EUR dışındaki "
          "dövizler çapraz kurdan türetildi. Veriler ECB internet sitesinden ücretsiz edinilebilir.")


def local_path() -> Path:
    """İnternetten güncellenen tablo: verilerle aynı yerel klasörde (OneDrive dışında), paketin içinde değil."""
    base = os.environ.get("LOCALAPPDATA") or Path.home() / ".local" / "share"
    return Path(base) / "KobiRadar" / "ecb_try_kurlari.csv"


def _read(path: Path) -> pd.DataFrame | None:
    try:
        return pd.read_csv(path, parse_dates=["date"]).set_index("date").sort_index()
    except (OSError, ValueError, KeyError):
        return None


@lru_cache(maxsize=1)
def raw_history() -> pd.DataFrame | None:
    """İş günü kurları; yerel (güncellenmiş) tablo paketle gelenden yeniyse o kullanılır."""
    tables = [t for t in (_read(DATA) if DATA.exists() else None,
                          _read(local_path()) if local_path().exists() else None) if t is not None and len(t)]
    return max(tables, key=lambda t: t.index.max()) if tables else None


@lru_cache(maxsize=1)
def history() -> pd.DataFrame | None:
    df = raw_history()
    return None if df is None else df.asfreq("D").ffill()       # hafta sonu ve tatil: bir önceki iş gününün kuru


def build_table(zf: zipfile.ZipFile) -> pd.DataFrame:
    """ECB eurofxref-hist.zip -> 1 birim döviz = kaç TL (EUR doğrudan, diğerleri çapraz kur), 2005'ten itibaren."""
    names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
    if len(names) != 1 or zf.getinfo(names[0]).file_size > MAX_CSV:
        raise ValueError("ECB dosyası beklenen biçimde değil.")
    df = pd.read_csv(zf.open(names[0]), parse_dates=["Date"])
    df = df.dropna(subset=["TRY"]).sort_values("Date").set_index("Date")
    df = df[df.index >= "2005-01-01"]                                   # 1 Ocak 2005: Yeni Türk Lirası
    out = pd.DataFrame({"EUR": df["TRY"]})
    for c in CURRENCIES:
        out[c] = df["TRY"] / df[c]
    out.index.name = "date"
    return out.round(6)


def validate(table: pd.DataFrame, today=None) -> None:
    """İndirilen tablo kullanılmadan önce denetlenir: sütunlar, uzunluk, pozitif değerler, tarih sırası, makul günlük
    değişim (TL hiçbir iş gününde %40'tan fazla oynamadı) ve paketle gelen tablodan daha eski olmaması."""
    today = pd.Timestamp(today or pd.Timestamp.now()).normalize()
    if list(table.columns) != ["EUR", *CURRENCIES] or len(table) < 4000:
        raise ValueError("ECB tablosu eksik.")
    if not table.index.is_monotonic_increasing or table.index.max() > today + pd.Timedelta(days=1):
        raise ValueError("ECB tablosunun tarihleri tutarsız.")
    vals = table[["EUR", "USD"]]
    if (vals <= 0).any().any() or vals.isna().any().any():
        raise ValueError("ECB tablosunda geçersiz kur var.")
    if (np.log(vals).diff().abs() > np.log(1.4)).any().any():
        raise ValueError("ECB tablosunda olağan dışı bir sıçrama var; dosya kullanılmadı.")
    bundled = _read(DATA) if DATA.exists() else None
    if bundled is not None and table.index.max() < bundled.index.max():
        raise ValueError("İndirilen tablo paketle gelenden eski.")


def update_from_ecb(timeout: float = 20.0) -> pd.Timestamp:
    """ECB'nin kur geçmişini indirir, denetler ve yerel tabloya yazar; tablonun son tarihini döndürür.
    Yalnızca kullanıcı düğmeye basınca çalışır. ECB'ye giden tek bilgi isteğin kendisidir (IP adresi); işletme
    verisi gönderilmez."""
    import requests                     # streamlit bağımlılığı; pakette var

    with requests.get(ECB_URL, timeout=timeout, stream=True) as r:
        r.raise_for_status()
        buf = io.BytesIO()
        for chunk in r.iter_content(65536):
            buf.write(chunk)
            if buf.tell() > MAX_DOWNLOAD:
                raise ValueError("ECB dosyası beklenenden büyük; indirme durduruldu.")
    table = build_table(zipfile.ZipFile(buf))
    validate(table)
    path = local_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    table.to_csv(tmp, float_format="%.6g")
    os.replace(tmp, path)
    clear_cache()
    return table.index.max()


def clear_cache() -> None:
    raw_history.cache_clear()
    history.cache_clear()
    conformal_k.cache_clear()


def latest(currencies=None) -> tuple[pd.Timestamp, dict[str, float]] | None:
    """Tablodaki son iş günü ve o günün kurları (bilgi amaçlı)."""
    df = raw_history()
    if df is None:
        return None
    row = df.iloc[-1]
    cur = [c for c in (currencies or df.columns) if c in df.columns and pd.notna(row.get(c))]
    return df.index.max(), {c: float(row[c]) for c in cur}


def typical_month_move(currency: str) -> float | None:
    """Son 3 yılda 30 günlük kur değişiminin %90'lık mutlak büyüklüğü (log); girilen kurun eskiliğini denetlemek için."""
    h = history()
    if h is None or currency not in h:
        return None
    x = np.log(h[currency].dropna().to_numpy())[-SHORT_WINDOW_DAYS:]
    if len(x) < 60:
        return None
    return float(np.quantile(np.abs(x[30:] - x[:-30]), 0.90))


def stale_rates(entered: dict[str, float]) -> list[tuple[str, float, float, float]]:
    """Girilen kuru ECB'nin son kurundan, son 3 yılın tipik bir aylık hareketinden (%90) fazla farklı olan dövizler:
    (döviz, girilen, ECB, fark oranı)."""
    info = latest(list(entered))
    if info is None:
        return []
    out = []
    for c, v in entered.items():
        ref, move = info[1].get(c), typical_month_move(c)
        if ref and move and v > 0 and abs(np.log(v / ref)) > move:
            out.append((c, v, ref, v / ref - 1))
    return out


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
        for j, c in enumerate(group):
            # Konformal genişletme: geçmişte bu yöntemin uçları %10'dan sık aşıldıysa bant o kadar açılır.
            k_lo, k_hi = (np.interp(t, CONFORMAL_H, [conformal_k(c, f"{pd.Timestamp(as_of):%Y-%m-%d}", hh, side,
                                                                 bool(window)) for hh in CONFORMAL_H])
                          for side in ("lo", "up"))
            med = np.median(path[:, :, j], axis=0)
            dev = path[:, :, j] - med
            out[c] = np.exp(med + np.where(dev > 0, k_hi * dev, k_lo * dev))
    return out


CONFORMAL_H = (30, 60, 90)
CONFORMAL_FROM = "2007-01-01"


@lru_cache(maxsize=256)
def conformal_k(currency: str, as_of: str, h: int, side: str, short: bool) -> float:
    """Konformal katsayı (split conformal; Vovk, Gammerman ve Shafer 2005). 2007'den bu yana, sonucu `as_of`'ta belli
    olan ve h gün arayla seçilmiş geçmiş tahmin günlerinde aynı yöntemle (yalnızca o güne kadarki veriyle) bant
    kurulur. Uç ile ortanca arasındaki uzaklık k ile çarpıldığında geçmiş aşım oranı %10'u geçmeyecek en küçük
    k (1-3) seçilir. ECB kurlarıyla sınama: seçim 2010-2017, sınav 2018-2026'da bir kez; borç tarafında (üst uç)
    aşım %10,3-13,2'den %7,5-11,4'e indi (docs/HATA_AZALTMA_ANALIZI.md, bölüm 7)."""
    x = np.log(history().loc[:pd.Timestamp(as_of), currency].dropna()).to_numpy()
    first = int(np.searchsorted(history().loc[:pd.Timestamp(as_of), currency].dropna().index, pd.Timestamp(CONFORMAL_FROM)))
    past = np.arange(first, len(x) - h, h)
    past = past[past >= MIN_HISTORY_DAYS]
    if len(past) < 20:
        return 1.0
    dist, real = [], []
    for p in past:
        hist = x[: p + 1][-SHORT_WINDOW_DAYS:] if short else x[: p + 1]
        r = hist[h:] - hist[:-h]
        if not short:
            r = r - r.mean()
        dist.append(np.quantile(r, [0.10, 0.50, 0.90]))
        real.append(x[p + h] - x[p])
    q, real = np.array(dist), np.array(real)
    for k in np.arange(1.0, 3.0001, 0.05):
        miss = (real > q[:, 1] + k * (q[:, 2] - q[:, 1])) if side == "up" else (real < q[:, 1] - k * (q[:, 1] - q[:, 0]))
        if miss.mean() <= 0.10:
            return float(k)
    return 3.0
