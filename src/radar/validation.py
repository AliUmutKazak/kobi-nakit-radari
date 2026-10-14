"""Simülasyon çalışması: tahmin, gerçeği bilinen çok sayıda sentetik şirkette sınanır.

Her şirket için veri tahmin tarihinden 90 gün sonrasına kadar üretilir, tahmin yalnızca
o güne kadarki bilgiyle yapılır ve sonra gerçekleşen kasa yoluyla karşılaştırılır.
Ölçülenler:
- Kasanın eksiye düşme olasılığı kalibre mi? (%30 denen şirketlerin ~%30'u düşmeli)
- Dönem sonu kasa, P10-P90 bandının içinde olması gereken sıklıkta mı kalıyor? (hedef %80)
- Beklenen değer sistematik olarak iyimser ya da kötümser mi?

Sentetik veriyi biz ürettiğimiz için bu çalışma modelin gerçek dünyada tutacağını
kanıtlamaz; kodun ve istatistiksel kurgunun kendi içinde tutarlı olduğunu ve hangi
şirket tiplerinde zorlandığını gösterir.

Şirketler arası fark büyüktür; bu yüzden her ölçüt bağımsız şirket sayısına göre standart
hatasıyla verilir. Standart hatanın içinde kalan bir fark bulgu sayılmaz.
"""
from __future__ import annotations

import itertools

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

from .pipeline import forecast
from .synthetic import cash_plan, generate, observe

REGIMES = {
    "customers": [8, 40],        # müşteri sayısı: yoğunlaşma riski
    "trend": [0.0, 1.2],         # gecikmelerin dönem içinde kötüleşme hızı
    "shock": [0.0, 0.3],         # çeyreklik ortak piyasa şoku (tahmin dönemindeki şok bilinmez)
}
OPENINGS = [0.2, 0.45, 0.8]      # açılış kasası (aylık ciro cinsinden); aynı tahminden türetilir


def run_case(seed: int, customers: int, trend: float, shock: float, as_of="2026-07-01",
             horizon: int = 90, n_sims: int = 1000, calib_hook=None) -> list[dict]:
    as_of = pd.Timestamp(as_of)
    end = as_of + pd.Timedelta(days=horizon)
    full = generate(seed=seed, n_customers=customers, as_of=end, trend=trend, shock=shock)
    obs = observe(full, as_of)
    _, outflows = cash_plan(obs, as_of, horizon)
    res = forecast(obs, as_of, 0.0, outflows, horizon, n_sims, seed=seed, calib_hook=calib_hook)
    sim = res["sim"]

    # Gerçekleşen yol: tahmin tarihinden sonra kesilenler dahil tüm faturaların gerçek ödeme günleri.
    paid = full[(full["true_paid_date"] > as_of) & (full["true_paid_date"] <= end)]
    flow = np.zeros(horizon + 1)
    np.add.at(flow, (paid["true_paid_date"] - as_of).dt.days.to_numpy(), paid["amount"].to_numpy())
    np.add.at(flow, (outflows["date"] - as_of).dt.days.to_numpy(), -outflows["amount"].to_numpy())
    truth = np.cumsum(flow)

    monthly = obs.loc[obs["issue_date"] > as_of - pd.Timedelta(days=180), "amount"].sum() / 6
    base = {"seed": seed, "customers": customers, "trend": trend, "shock": shock, "n_invoices": len(obs),
            "simple_model": res["simple_model"], "rho_market": res["ctx"]["calib"]["rho_market"], "rho_customer": res["ctx"]["calib"]["rho_customer"],
            "z_shift": res["ctx"]["calib"]["fresh"]["z_shift"], "z_shift_overdue": res["ctx"]["calib"]["overdue"]["z_shift"],
            "z_scale": res["ctx"]["calib"]["fresh"]["z_scale"], "z_scale_overdue": res["ctx"]["calib"]["overdue"]["z_scale"],
            "err_p50_months": (sim.p50[-1] - truth[-1]) / monthly,
            "inside": bool(sim.p10[-1] <= truth[-1] <= sim.p90[-1]),
            "below": bool(truth[-1] < sim.p10[-1]), "above": bool(truth[-1] > sim.p90[-1])}
    # Açılış kasası yalnızca tüm yolları sabit kadar kaydırır; aynı senaryolardan üç ayrı şirket durumu çıkar.
    return [base | {"opening_months": m, "p_breach": float((sim.min_balance + m * monthly < 0).mean()),
                    "breached": bool(truth[1:].min() + m * monthly < 0)} for m in OPENINGS]


def study(seeds=range(24), n_jobs: int = -1, **kwargs) -> pd.DataFrame:
    grid = list(itertools.product(seeds, *REGIMES.values()))
    rows = Parallel(n_jobs=n_jobs)(delayed(run_case)(s, c, t, k, **kwargs) for s, c, t, k in grid)
    return pd.DataFrame([r for case in rows for r in case])


def _rate(x: pd.Series) -> str:
    """Oran ve standart hatası (yüzde puan)."""
    p, n = x.mean(), len(x)
    return f"%{p * 100:.0f} ±{np.sqrt(p * (1 - p) / n) * 100:.0f}"


def summarize(df: pd.DataFrame) -> dict:
    cases = df[df["opening_months"] == OPENINGS[0]]          # bant ölçütleri açılıştan bağımsız: tahmin başına bir satır
    bins = pd.cut(df["p_breach"], [-0.01, 0.1, 0.3, 0.7, 0.9, 1.0], labels=["0-10", "10-30", "30-70", "70-90", "90-100"])
    reliability = df.groupby(bins, observed=True).agg(n=("breached", "size"), tahmin=("p_breach", "mean"),
                                                       gerceklesen=("breached", "mean"))
    base = df["breached"].mean()

    def table(col):
        g = cases.groupby(col)
        return pd.DataFrame({"n": g.size(), "bant_ici": g["inside"].apply(_rate), "altinda": g["below"].apply(_rate),
                             "ustunde": g["above"].apply(_rate),
                             "sapma_ay": g["err_p50_months"].apply(lambda x: f"{x.mean():+.2f} ±{x.std() / np.sqrt(len(x)):.2f}"),
                             "rho_piyasa": g["rho_market"].mean().round(2), "rho_musteri": g["rho_customer"].mean().round(2),
                             "kayma": g["z_shift"].mean().round(2), "kayma_gecikmis": g["z_shift_overdue"].mean().round(2),
                             "olcek": g["z_scale"].mean().round(2), "olcek_gecikmis": g["z_scale_overdue"].mean().round(2)})

    err = cases["err_p50_months"]
    return {
        "n_cases": len(cases), "n_rows": len(df),
        "coverage": _rate(cases["inside"]), "below_p10": _rate(cases["below"]), "above_p90": _rate(cases["above"]),
        "bias_months": f"{err.mean():+.2f} ±{err.std() / np.sqrt(len(err)):.2f}",
        "brier": float(np.mean((df["p_breach"] - df["breached"]) ** 2)),
        "brier_baseline": float(base * (1 - base)),
        "reliability": reliability,
        "by_regime": {k: table(k) for k in REGIMES},
    }
