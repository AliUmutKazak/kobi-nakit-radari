"""ECB euro referans kurlarından (eurofxref-hist.zip) 1 birim döviz = kaç TL tablosunu üretir.

Kaynak: Avrupa Merkez Bankası, https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.zip
Kullanım koşulu (ECB internet sitesi, Copyright): bilgi kaynak gösterilerek serbestçe kullanılabilir; değiştirilmişse
bu açıkça belirtilmelidir. Burada yapılan değişiklik: EUR dışındaki dövizlerin TL karşılığı, ECB'nin euro bazlı
kurlarından çapraz kur olarak türetilir (ör. USD/TRY = EUR/TRY ÷ EUR/USD). Boş günler doldurulmaz; panel
(radar.fx) bir önceki iş gününü kullanır.

Kullanım: python tools/ecb_kurlari.py indirilen/eurofxref-hist.zip
"""
import sys
import zipfile
from pathlib import Path

import pandas as pd

CURRENCIES = ("USD", "GBP", "CHF", "CNY")
OUT = Path(__file__).resolve().parents[1] / "src" / "radar" / "data" / "ecb_try_kurlari.csv"


def main(path: str) -> None:
    z = zipfile.ZipFile(path)
    df = pd.read_csv(z.open(z.namelist()[0]), parse_dates=["Date"])
    df = df.dropna(subset=["TRY"]).sort_values("Date").set_index("Date")
    df = df[df.index >= "2005-01-01"]                  # 1 Ocak 2005: Yeni Türk Lirası
    out = pd.DataFrame({"EUR": df["TRY"]})
    for c in CURRENCIES:
        out[c] = df["TRY"] / df[c]
    out.index.name = "date"
    out.round(6).to_csv(OUT, float_format="%.6g")
    print(f"{OUT.name}: {out.index.min():%Y-%m-%d} - {out.index.max():%Y-%m-%d}, {len(out)} gün")


if __name__ == "__main__":
    main(sys.argv[1])
