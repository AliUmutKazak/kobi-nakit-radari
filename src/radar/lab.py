"""Senaryo laboratuvarı: tahmin, kaynaklara dayanan çok boyutlu bir senaryo uzayında sınanır.

Amaç ezber değil genelleme: model hiçbir senaryoda eğitilmez; her sentetik işletmede yalnızca o işletmenin
tahmin gününe kadarki geçmişiyle kurulur (gerçek kullanımdaki gibi) ve 90 gün sonra gerçekleşenle
karşılaştırılır. Senaryolar yalnızca sınavdır.

Boyutlar ve dayanakları (aralıkların kaynağı RANGES içinde; varsayım olanlar açıkça yazılı):
- Ölçek ve sektör: TCMB–TÜİK Sektör Bilançoları 2025 (benchmark.py). Her senaryoda ölçeğe uygun bir
  iki haneli sektör seçilir; hedef tahsil süresi o sektörün çeyrekler arası aralığından çekilir ve
  gecikmeler bu hedefe oturacak biçimde ölçeklenir. Müşteri sayısı aralıkları varsayımdır.
- Mevsimsellik: gerçek bir KOBİ'nin iki yıllık satışında genlik 0,30 (UCI Online Retail II).
- Enflasyon: TÜİK TÜFE yıllık değişimi 2021-2025 arasında yaklaşık %20 ile %85 arasında gezdi.
  Fatura tutarlarının enflasyonla arttığı varsayılır.
- Müşteri yoğunlaşması: gerçek KOBİ'de 40 müşterilik alt örneklemlerde Gini 0,56-0,70 (çeyrekler arası);
  size_sigma bu aralığı üretecek biçimde seçildi.
- Geçmiş uzunluğu, kötüleşme, şok: varsayım (ürünün karşılaşacağı işletme çeşitliliği).
- Çek: karşılıksızlık oranı TBB Risk Merkezi'nden; çekle ödeyen müşteri payı ve çek vadesi için kurumsal
  istatistik bulunamadı (varsayım). Ürün bu iki değeri her işletmenin kendi cari hesabından öğrenir
  (pipeline.cheque_habits); laboratuvar geniş bir aralıkta bu öğrenmenin tuttuğunu sınar.

Geliştirme ve sınav ayrımı:
- "gelistirme": yöntem değişiklikleri yalnızca burada denenir. Tohumlar 100000'den başlar.
- "sinav": hiç bakılmadan saklanır, yalnızca bir sürüm tamamlandığında koşulur. Tohumlar 500000'den başlar
  ve senaryoların yarısında tek bir boyut geliştirme aralığının DIŞINDAN çekilir (saklı rejim). Her sınav
  koşusu docs/lab/sinav_kaydi.csv'ye tarih ve sürümle yazılır: sınava kaç kez bakıldığı görünür kalır.
"""
from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from scipy.stats import qmc

from . import benchmark
from .actions import metrics
from scipy import stats

from .standards import SIGNIFICANCE, basel_zone, benjamini_hochberg, kupiec_pof, spiegelhalter
from .synthetic import generate, observe
from .validation import OPENINGS, run_case

AS_OF = pd.Timestamp("2026-01-01")        # tahmin günü bu tarihten itibaren yılın rastgele bir günü (as_of_day)
HORIZON = 90
SEED_BASE = {"gelistirme": 100_000, "sinav": 500_000}
CUSTOMERS = {"mikro": (5, 15), "kucuk": (15, 50), "orta": (50, 120)}     # varsayım: vadeli satış yapılan müşteri sayısı
SIZE_SHARE = {"mikro": 0.35, "kucuk": 0.40, "orta": 0.25}

# boyut: (geliştirme aralığı, saklı aralık, dayanak)
RANGES = {
    "season_amp": ((0.0, 0.30), (0.30, 0.45), "UCI Online Retail II: gerçek KOBİ'de genlik 0,30"),
    "inflation": ((0.0, 0.50), (0.50, 0.85), "TÜİK TÜFE yıllık, 2021-2025: ~%20-%85"),
    "size_sigma": ((0.6, 1.3), (1.3, 1.7), "Online Retail II alt örneklemleri: Gini 0,56-0,70"),
    "history": ((15, 36), (8, 15), "varsayım: işletmenin sisteme verdiği geçmiş (ay)"),
    "trend": ((0.0, 1.2), (1.2, 1.8), "varsayım: gecikmelerin dönem içinde kötüleşmesi"),
    "shock": ((0.0, 0.30), (0.30, 0.45), "varsayım: çeyreklik ortak piyasa şoku"),
    "cheque_share": ((0.0, 0.60), (0.60, 0.90), "varsayım: çekle ödeyen müşteri payı (kurumsal istatistik yok)"),
    "cheque_term": ((30, 120), (120, 180), "varsayım: çek vadesi ortancası, gün (kurumsal istatistik yok)"),
    "cheque_bounce": ((0.028, 0.034), (0.034, 0.07), "TBB Risk Merkezi 2026: tutar bazında %2,8-3,4; saklı: kriz"),
    "record_lag": ((0, 14), (14, 31), "VUK m.219: kayıt en geç 10 gün, fişe dayanan kayıtta 45 gün; aralık varsayım"),
    "partial_share": ((0.0, 0.40), (0.40, 0.70), "varsayım: faturalarını iki taksitte kapatan müşteri payı"),
    "missing_due": ((0.0, 0.30), (0.30, 0.60), "veri kalitesi: vadesi girilmemiş fatura payı (TTK m.1530/4-a: 30 gün)"),
    "outflow_sigma": ((0.0, 0.30), (0.30, 0.50), "varsayım: aylık giderlerin dalgalanması (log ölçekte sapma)"),
    "as_of_day": ((0, 364), (0, 364), "tahmin günü: 2026 içinde yılın günü (ayın başı, ortası, sonu)"),
}
DSO_LIMITS = (15.0, 180.0)        # üreticinin ulaşabildiği aralık; dışı kırpılır ve raporlanır
LOG = Path(__file__).resolve().parents[2] / "docs" / "lab" / "sinav_kaydi.csv"


def sample(split: str, n: int, seed: int = 0, focus: dict | None = None) -> pd.DataFrame:
    """Latin hiperküp örneklemesi: her boyut kendi aralığında eşit dağılımla kaplanır.

    focus: {boyut: (alt, üst)} odak çalışması; sınavın gösterdiği bir zayıf bölge geliştirme tarafında yeni
    tohumlarla incelenir (sınav verisiyle ayar yapılmaz)."""
    if split not in SEED_BASE:
        raise ValueError(split)
    rng = np.random.default_rng(SEED_BASE[split] + seed)
    u = qmc.LatinHypercube(d=len(RANGES) + 3, seed=rng).random(n)
    if not benchmark.available():
        raise FileNotFoundError(f"Senaryo laboratuvarı TCMB sektör tablosunu gerektirir: {benchmark.TABLE} "
                                "(yeniden dağıtılamadığı için depoda yok).")
    sectors = benchmark.table()
    sectors = sectors[sectors["duzey"] != "bölüm"]
    rows = []
    for i in range(n):
        size = list(SIZE_SHARE)[int(np.searchsorted(np.cumsum(list(SIZE_SHARE.values())), u[i, 0]))]
        lo_c, hi_c = CUSTOMERS[size]
        row = {"case": i, "seed": SEED_BASE[split] + seed * 10_000 + i, "split": split, "olcek": size,
               "customers": int(round(np.exp(np.log(lo_c) + u[i, 1] * (np.log(hi_c) - np.log(lo_c)))))}
        pool = sectors[sectors["olcek"] == size]
        sec = pool.iloc[int(u[i, 2] * len(pool))]
        # Hedef tahsil süresi: sektörün iyi ve kötü çeyrek sınırları arasında log ölçekte eşit dağılım.
        dso = float(np.exp(np.log(sec["gun_iyi"]) + rng.random() * (np.log(sec["gun_kotu"]) - np.log(sec["gun_iyi"]))))
        row |= {"sektor": sec["kod"], "dso_sektor": dso, "dso_hedef": float(np.clip(dso, *DSO_LIMITS))}
        held = rng.choice([k for k in RANGES if k != "as_of_day"]) if split == "sinav" and i % 2 == 1 else None
        for j, (name, (dev, out, _)) in enumerate(RANGES.items()):
            lo, hi = (focus or {}).get(name, out if name == held else dev)
            row[name] = lo + u[i, 3 + j] * (hi - lo)
        row["history"] = int(round(row["history"]))
        row["record_lag"] = int(round(row["record_lag"]))
        row["as_of_day"] = int(row["as_of_day"])
        row["as_of"] = AS_OF + pd.Timedelta(days=row["as_of_day"])
        row["ayin_gunu"] = int(row["as_of"].day)               # ay başı tahminlerinde ay sonu ödemeleri yakın
        row["saklı_boyut"] = held or ""
        row["season_peak"] = int(rng.integers(1, 13))
        rows.append(row)
    return pd.DataFrame(rows)


def _gen(row, delay_scale: float = 1.0) -> dict:
    return {"months": int(row["history"]) + 3, "season_amp": float(row["season_amp"]),
            "season_peak": int(row["season_peak"]), "inflation": float(row["inflation"]),
            "size_sigma": float(row["size_sigma"]), "delay_scale": delay_scale, "terms_scale": min(1.0, delay_scale),
            "cheque_share": float(row["cheque_share"]), "cheque_term": float(row["cheque_term"]),
            "cheque_bounce": float(row["cheque_bounce"]), "record_lag": int(row["record_lag"]),
            **{k: float(row[k]) for k in ("partial_share", "missing_due", "outflow_sigma") if k in row}}


def dso(obs: pd.DataFrame, as_of, doubtful_days: int = 180) -> float:
    """Bilanço tanımına yakın tahsil süresi: vadesini 180 günden fazla geçmiş açık alacaklar şüpheli alacak
    sayılıp dışarıda bırakılır (Tekdüzen Hesap Planı'nda 128 şüpheli ticari alacaklar 129 karşılıkla
    netleşir; TCMB oranı bu net tutara dayanır). Paneldeki tahsil süresi (actions.metrics) bunları içerir."""
    as_of = pd.Timestamp(as_of)
    keep = ~((obs["open_amount"] > 0) & (obs["due_date"] < as_of - pd.Timedelta(days=doubtful_days)))
    return metrics(obs[keep], as_of)["dso"]


def fit_delay_scale(row, iters: int = 8) -> tuple[float, float]:
    """Tahsil süresi hedefe oturana kadar gecikme ölçeği ikiye bölmeyle aranır; ölçek 1'in altına inince vadeler
    de aynı oranda kısalır (peşine yakın satış yapan sektörler). Aynı tohumda tahsil süresi ölçekle tekdüze
    artar. Dönen: (ölçek, ulaşılan tahsil süresi, gün)."""
    def measure(scale):
        gen = _gen(row, scale)
        gen.pop("record_lag"); gen.pop("missing_due", None); gen.pop("outflow_sigma", None)
        as_of = pd.Timestamp(row["as_of"])
        full = generate(seed=int(row["seed"]), n_customers=int(row["customers"]), as_of=as_of,
                        trend=float(row["trend"]), shock=float(row["shock"]), **gen)
        return dso(observe(full, as_of), as_of)
    lo, hi = np.log(0.2), np.log(10.0)
    for _ in range(iters):
        mid = (lo + hi) / 2
        if measure(np.exp(mid)) < row["dso_hedef"]:
            lo = mid
        else:
            hi = mid
    scale = float(np.exp((lo + hi) / 2))
    return scale, float(measure(scale))


def run_one(row: dict, n_sims: int = 1000, forecast_kwargs: dict | None = None) -> list[dict]:
    scale, achieved = fit_delay_scale(row)
    out = run_case(int(row["seed"]), int(row["customers"]), float(row["trend"]), float(row["shock"]),
                   as_of=pd.Timestamp(row["as_of"]), horizon=HORIZON, n_sims=n_sims, gen=_gen(row, scale), forecast_kwargs=forecast_kwargs)
    return [r | {k: row[k] for k in row if k not in r} | {"delay_scale": scale, "dso": achieved} for r in out]


def run(split: str = "gelistirme", n: int = 200, seed: int = 0, n_jobs: int = -1, n_sims: int = 1000,
        confirm_test: bool = False, focus: dict | None = None, forecast_kwargs: dict | None = None) -> pd.DataFrame:
    """forecast_kwargs: bir düzeltmenin etkisini aynı senaryolarda ölçmek için (ör. {"cheque_aware": False})."""
    if split == "sinav" and not confirm_test:
        raise PermissionError("Sınav kümesi yalnızca bir sürüm tamamlandığında ve açık onayla koşulur (confirm_test=True).")
    spec = sample(split, n, seed, focus)
    rows = Parallel(n_jobs=n_jobs)(delayed(run_one)(r, n_sims, forecast_kwargs) for r in spec.to_dict("records"))
    df = pd.DataFrame([r for case in rows for r in case])
    if split == "sinav":
        from .pilot import VERSION
        LOG.parent.mkdir(parents=True, exist_ok=True)
        entry = pd.DataFrame([{"tarih": dt.datetime.now().isoformat(timespec="seconds"), "surum": VERSION,
                               "n": n, "seed": seed}])
        entry.to_csv(LOG, mode="a", header=not LOG.exists(), index=False, encoding="utf-8")
    return df


def bin_report(cases: pd.DataFrame, rows: pd.DataFrame, by: pd.Series) -> pd.DataFrame:
    """Her senaryo kesiti için uluslararası testler. cases: tahmin başına bir satır; rows: açılış düzeyleriyle."""
    out = []
    for key, part in cases.groupby(by, observed=True):
        n, below, above = len(part), int(part["below"].sum()), int(part["above"].sum())
        r = rows[rows["seed"].isin(part["seed"])]
        sp = spiegelhalter(r["p_breach"], r["breached"]) if r["breached"].nunique() > 1 else {"p_value": float("nan")}
        d = part["err_final_model"] - part["err_final_medyan"]
        out.append({"kesit": key, "n": n, "alt_aşım": below / n, "üst_aşım": above / n,
                    "basel": basel_zone(n, below, 0.10)["zone"], "kupiec_alt_p": kupiec_pof(n, below, 0.10)["p_value"],
                    "kupiec_üst_p": kupiec_pof(n, above, 0.10)["p_value"],
                    "sapma_ay": part["err_p50_months"].mean(), "hata_ay": part["err_final_model"].mean(),
                    "fark_medyan": d.mean(), "fark_se": d.std(ddof=1) / np.sqrt(n) if n > 1 else float("nan"),
                    "spiegelhalter_p": sp["p_value"]})
    return pd.DataFrame(out).set_index("kesit")


def robustness_map(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Sağlamlık haritası: her boyut üç eşit sayılı kesite bölünür; saklı rejim (sınavda) ayrı kesittir."""
    cases = df[df["opening_months"] == OPENINGS[0]]
    maps = {"genel": bin_report(cases, df, pd.Series("tümü", index=cases.index)),
            "olcek": bin_report(cases, df, cases["olcek"])}
    for name in [k for k in RANGES if k != "as_of_day"] + ["ayin_gunu", "dso", "customers"]:
        inside = cases["saklı_boyut"].ne(name) if "saklı_boyut" in cases else pd.Series(True, index=cases.index)
        labels = pd.Series("4) saklı (geliştirme aralığı dışı)", index=cases.index, dtype=object)
        x = cases.loc[inside, name]
        edges = np.unique(np.quantile(x, [0, 1 / 3, 2 / 3, 1]))
        fmt = ((lambda v: f"{v:.0f}") if name in ("history", "dso", "customers", "cheque_term", "record_lag", "ayin_gunu")
               else (lambda v: f"{v:.3f}") if name == "cheque_bounce" else (lambda v: f"{v:.2f}"))
        idx = np.clip(np.searchsorted(edges, x, side="right") - 1, 0, len(edges) - 2)
        labels.loc[inside] = [f"{i + 1}) {fmt(edges[i])}–{fmt(edges[i + 1])}" for i in idx]
        maps[name] = bin_report(cases, df, labels)
    if "saklı_boyut" in cases and cases["saklı_boyut"].ne("").any():
        maps["saklı_rejim"] = bin_report(cases, df, cases["saklı_boyut"].replace("", "geliştirme aralığı içi"))
    return maps


def realism(df: pd.DataFrame) -> dict:
    """Katman 2 denetimi: üretilen senaryolar kaynaklara gerçekten oturuyor mu?"""
    cases = df[df["opening_months"] == OPENINGS[0]]
    gap = (cases["dso"] - cases["dso_hedef"]).abs() / cases["dso_hedef"]
    return {"dso_hedef_medyan": float(cases["dso_hedef"].median()), "dso_ulasilan_medyan": float(cases["dso"].median()),
            "dso_sapma_medyan": float(gap.median()), "dso_10pct_icinde": float((gap <= 0.10).mean()),
            "dso_kirpilan": float((cases["dso_sektor"] != cases["dso_hedef"]).mean())}


def weak_spots(maps: dict[str, pd.DataFrame]) -> list[str]:
    """Zayıf bölge: kötümser uçta Basel sarı/kırmızı, ya da Kupiec alt uç reddi veya basit yöntemden anlamlı
    kötülük. Onlarca kesit birlikte sınandığı için Kupiec ve karşılaştırma p değerleri Benjamini-Hochberg ile
    düzeltilir (şansla reddedilen kesitler zayıf sayılmaz); Basel bölgesi ihtiyat gereği düzeltilmez."""
    items = []
    for dim, t in maps.items():
        for key, r in t.iterrows():
            z = r["fark_medyan"] / r["fark_se"] if r["fark_se"] and r["fark_se"] == r["fark_se"] else float("nan")
            items.append((dim, key, r, r["kupiec_alt_p"], float(stats.norm.sf(z)) if z == z else float("nan")))
    q = benjamini_hochberg([i[3] for i in items] + [i[4] for i in items])
    q_kup, q_cmp = q[:len(items)], q[len(items):]
    out = []
    for (dim, key, r, _, _), qk, qc in zip(items, q_kup, q_cmp):
        why = []
        if r["basel"] != "yeşil":
            why.append(f"Basel {r['basel']}")
        if qk < SIGNIFICANCE:
            why.append(f"Kupiec alt q={qk:.3f}")
        if qc < SIGNIFICANCE:
            why.append(f"basit yöntemden anlamlı kötü (q={qc:.3f})")
        if why:
            out.append(f"{dim} = {key} (n={int(r['n'])}): " + ", ".join(why))
    return out


def _md(t: pd.DataFrame) -> str:
    cols = ["n", "alt_aşım", "üst_aşım", "basel", "kupiec_alt_p", "kupiec_üst_p", "sapma_ay", "hata_ay", "fark_medyan", "spiegelhalter_p"]
    head = "| kesit | " + " | ".join(cols) + " |\n|" + "---|" * (len(cols) + 1) + "\n"
    body = ""
    for key, r in t.iterrows():
        cells = []
        for c in cols:
            v = r[c]
            if c in ("alt_aşım", "üst_aşım"):
                cells.append(f"%{v * 100:.0f}")
            elif c == "fark_medyan":
                cells.append(f"{v:+.2f} ±{r['fark_se']:.2f}")
            elif isinstance(v, float):
                cells.append(f"{v:.3f}" if "p" in c else f"{v:+.2f}" if c == "sapma_ay" else f"{v:.2f}")
            else:
                cells.append(str(v))
        body += f"| {key} | " + " | ".join(cells) + " |\n"
    return head + body


def report(df: pd.DataFrame) -> str:
    split = df["split"].iloc[0]
    maps = robustness_map(df)
    real = realism(df)
    weak = weak_spots(maps)
    lines = [f"## Senaryo laboratuvarı: {split} kümesi ({df['seed'].nunique()} sentetik işletme)", "",
             "Sütunlar: alt/üst aşım = dönem sonu kasa P10'un altında / P90'ın üstünde kalma oranı (hedef %10); "
             "Basel = kötümser uç trafik ışığı; Kupiec p < 0,05 aşım oranının %10'dan farklı olduğunu gösterir; "
             "sapma ve hata aylık ciro cinsinden; fark_medyan = modelin dönem sonu hatası eksi \"müşteri her zamanki "
             "kadar geç öder\" yönteminin hatası (eksi = model daha iyi, ± standart hata); Spiegelhalter p < 0,05 "
             "eksiye düşme olasılıklarının kalibre olmadığını gösterir.", "",
             f"Gerçekçilik denetimi: hedef tahsil süresi medyanı {real['dso_hedef_medyan']:.0f} gün, ulaşılan "
             f"{real['dso_ulasilan_medyan']:.0f} gün; senaryoların %{real['dso_10pct_icinde'] * 100:.0f}'i hedefin "
             f"±%10'u içinde; sektör değeri üreticinin aralığı dışında kaldığı için kırpılan: "
             f"%{real['dso_kirpilan'] * 100:.0f}.", ""]
    raw = sum(int((t["kupiec_alt_p"] < SIGNIFICANCE).sum()) for t in maps.values())
    lines += ["### Zayıf bölgeler", "",
              f"Ham Kupiec alt uç p < 0,05 olan kesit sayısı: {raw} / {sum(len(t) for t in maps.values())} (çoklu "
              "testte şansla beklenen ~%5). Aşağıdaki liste Benjamini-Hochberg düzeltmesinden sonra kalanlardır.", ""]
    lines += ([f"- {w}" for w in weak] or ["- Yok."]) + [""]
    for dim, t in maps.items():
        src = RANGES[dim][2] if dim in RANGES else ""
        lines += [f"### {dim}" + (f" ({src})" if src else ""), "", _md(t), ""]
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Senaryo laboratuvarı")
    ap.add_argument("--bolum", choices=list(SEED_BASE), default="gelistirme")
    ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--sinav-onayi", action="store_true")
    ap.add_argument("--cikti", default=None, help="sonuç tablosu (.csv)")
    a = ap.parse_args(argv)
    df = run(a.bolum, a.n, a.seed, confirm_test=a.sinav_onayi)
    if a.cikti:
        df.to_csv(a.cikti, index=False, encoding="utf-8")
    print(report(df))


if __name__ == "__main__":
    main()
