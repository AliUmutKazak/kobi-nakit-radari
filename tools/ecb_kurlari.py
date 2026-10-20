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

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from radar import fx  # noqa: E402

OUT = fx.DATA


def main(path: str) -> None:
    out = fx.build_table(zipfile.ZipFile(path))
    fx.validate(out)
    out.to_csv(OUT, float_format="%.6g")
    print(f"{OUT.name}: {out.index.min():%Y-%m-%d} - {out.index.max():%Y-%m-%d}, {len(out)} gün")


if __name__ == "__main__":
    main(sys.argv[1])
