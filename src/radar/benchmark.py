"""Türkiye'de sektör ve ölçeğe göre alacak tahsil süresi karşılaştırması.

Kaynak: TCMB ve TÜİK, Sektör Bilançoları İstatistikleri 2023-2025, "Standart oranlar tablosu" (kartil),
ölçek kırılımı; Alacak Devir Hızı (kez) = net satışlar / ortalama ticari alacaklar. Veriler vergi
idaresine verilen bilanço ve gelir tablolarından derlenir (yaklaşık 1 milyon girişim). İndirme:
tcmb.gov.tr > İstatistikler > Reel Sektör İstatistikleri > Sektör Bilançoları > "Dosya 2" (17.10.2026;
SHA-256 b0e93563...). Tahsil süresi = 365 / devir hızı; devir hızının üst çeyreği en iyi (en kısa
süreli) çeyrektir. Tablo: data/sektor_alacak_2025.csv (2025 yılı değerleri).

Karşılaştırma bilgi amaçlıdır: TCMB oranı yıllık ortalama ticari alacağa dayanır, paneldeki tahsil süresi
bugünkü açık alacağın son 90 günün satışına oranıdır; tanımlar yakındır ama aynı değildir.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pandas as pd

SIZES = {"mikro": "Mikro", "kucuk": "Küçük", "orta": "Orta", "buyuk": "Büyük"}
SOURCE = "TCMB–TÜİK Sektör Bilançoları, 2025"


@lru_cache(maxsize=1)
def table() -> pd.DataFrame:
    return pd.read_csv(Path(__file__).parent / "data" / "sektor_alacak_2025.csv", dtype={"kod": str}, encoding="utf-8")


def sectors() -> list[tuple[str, str]]:
    """(kod, görünen ad): önce bölümler (harf), sonra iki haneli sektörler."""
    t = table().drop_duplicates(["duzey", "kod"])
    t = t.assign(sira=(t["duzey"] != "bölüm").astype(int)).sort_values(["sira", "kod"])
    return [(r.kod, f"{r.kod} – {r.sektor.capitalize() if r.sektor.isupper() else r.sektor}") for r in t.itertuples()]


def lookup(code: str, size: str) -> dict | None:
    t = table()
    hit = t[(t["kod"] == str(code)) & (t["olcek"] == size)]
    if hit.empty:
        return None
    r = hit.iloc[0]
    return {"kod": r["kod"], "sektor": r["sektor"], "olcek": SIZES.get(size, size), "firma": int(r["firma"]),
            "medyan_gun": float(r["gun_q2"]), "iyi_ceyrek_gun": float(r["gun_iyi"]), "kotu_ceyrek_gun": float(r["gun_kotu"])}


def compare(dso_days: float, code: str, size: str) -> str | None:
    """İşletmenin tahsil süresinin sektördeki yeri, tek cümle."""
    b = lookup(code, size)
    if b is None or dso_days != dso_days:
        return None
    if dso_days <= b["iyi_ceyrek_gun"]:
        where = "en iyi çeyrekte (en hızlı tahsil eden %25)"
    elif dso_days <= b["medyan_gun"]:
        where = "ortancadan iyi"
    elif dso_days <= b["kotu_ceyrek_gun"]:
        where = "ortancadan kötü"
    else:
        where = "en kötü çeyrekte (en yavaş tahsil eden %25)"
    return (f"Ortalama tahsil süreniz {dso_days:.0f} gün: sektörünüzde ({b['sektor']}, {b['olcek'].lower()} ölçek, "
            f"{b['firma']:,} firma) ortanca {b['medyan_gun']:.0f} gün, en iyi çeyrek {b['iyi_ceyrek_gun']:.0f} günden kısa, "
            f"en kötü çeyrek {b['kotu_ceyrek_gun']:.0f} günden uzun. Siz {where}. Kaynak: {SOURCE}.").replace(",", ".")
