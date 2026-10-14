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
"""
from __future__ import annotations

import itertools

import numpy as np
import pandas as pd

from .pipeline import forecast
from .synthetic import cash_plan, generate, observe

REGIMES = {
    "customers": [8, 20, 40],            # müşteri sayısı: yoğunlaşma riski
    "trend": [0.0, 0.6, 1.2],            # gecikmelerin dönem içinde kötüleşme hızı
    "opening_months": [0.2, 0.45, 0.8],  # açılış kasası (aylık ciro cinsinden)
}


def run_case(seed: int, customers: int, trend: float, opening_months: float, as_of="2026-07-01",
             horizon: int = 90, n_sims: int = 1000) -> dict:
    as_of = pd.Timestamp(as_of)
    end = as_of + pd.Timedelta(days=horizon)
    full = generate(seed=seed, n_customers=customers, as_of=end, trend=trend)
    obs = observe(full, as_of)
    opening, outflows = cash_plan(obs, as_of, horizon, opening_months)
    sim = forecast(obs, as_of, opening, outflows, horizon, n_sims, seed=seed)["sim"]

    # Gerçekleşen yol: tahmin tarihinden sonra kesilenler dahil tüm faturaların gerçek ödeme günleri.
    paid = full[(full["true_paid_date"] > as_of) & (full["true_paid_date"] <= end)]
    flow = np.zeros(horizon + 1)
    np.add.at(flow, (paid["true_paid_date"] - as_of).dt.days.to_numpy(), paid["amount"].to_numpy())
    np.add.at(flow, (outflows["date"] - as_of).dt.days.to_numpy(), -outflows["amount"].to_numpy())
    truth = opening + np.cumsum(flow)

    scale = obs.loc[obs["issue_date"] > as_of - pd.Timedelta(days=180), "amount"].sum() / 6   # aylık ciro
    return {"seed": seed, "customers": customers, "trend": trend, "opening_months": opening_months,
            "n_invoices": len(obs), "p_breach": sim.prob_any_breach, "breached": bool(truth.min() < 0),
            "final_truth": truth[-1], "final_p10": sim.p10[-1], "final_p50": sim.p50[-1], "final_p90": sim.p90[-1],
            "err_p50_months": (sim.p50[-1] - truth[-1]) / scale}


def study(seeds=range(3), **kwargs) -> pd.DataFrame:
    grid = itertools.product(seeds, *REGIMES.values())
    return pd.DataFrame([run_case(s, c, t, o, **kwargs) for s, c, t, o in grid])


def summarize(df: pd.DataFrame) -> dict:
    bins = pd.cut(df["p_breach"], [-0.01, 0.1, 0.3, 0.7, 0.9, 1.0], labels=["0-10", "10-30", "30-70", "70-90", "90-100"])
    reliability = df.groupby(bins, observed=True).agg(n=("breached", "size"), tahmin=("p_breach", "mean"),
                                                       gerceklesen=("breached", "mean"))
    base = df["breached"].mean()
    inside = (df["final_truth"] >= df["final_p10"]) & (df["final_truth"] <= df["final_p90"])
    by = lambda col: df.assign(inside=inside).groupby(col).agg(
        n=("inside", "size"), bant_ici=("inside", "mean"), sapma_ay=("err_p50_months", "mean"),
        tahmin=("p_breach", "mean"), gerceklesen=("breached", "mean"))
    return {
        "n": len(df),
        "brier": float(np.mean((df["p_breach"] - df["breached"]) ** 2)),
        "brier_baseline": float(base * (1 - base)),
        "coverage": float(inside.mean()),
        "below_p10": float((df["final_truth"] < df["final_p10"]).mean()),
        "above_p90": float((df["final_truth"] > df["final_p90"]).mean()),
        "bias_months": float(df["err_p50_months"].mean()),
        "reliability": reliability,
        "by_regime": {k: by(k) for k in REGIMES},
    }
