"""Uçtan uca akış: veri -> model -> simülasyon -> öncelikli tahsilat listesi, ve geri testler."""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import actions
from .features import build_features
from .model import DelayModel, FallbackModel, evaluate, fit_model, training_frame
from .simulate import aging_curve, simulate
from .synthetic import cash_plan, observe


def default_rates(obs: pd.DataFrame, as_of, prior_n: float = 20.0) -> pd.Series:
    """Müşteri bazında tahsil edilememe oranı: vadesi 180+ gün geçmiş faturalardan, büzülmüş."""
    old = obs[obs["due_date"] <= pd.Timestamp(as_of) - pd.Timedelta(days=180)]
    bad = old["paid_date"].isna()
    g = bad.mean() if len(old) else 0.02
    by = bad.groupby(old["customer_id"]).agg(["sum", "count"])
    rate = (by["sum"] + prior_n * g) / (by["count"] + prior_n)
    return rate.reindex(obs["customer_id"].unique()).fillna(g)


def project_sales(obs: pd.DataFrame, as_of, horizon: int) -> pd.DataFrame:
    """Henüz kesilmemiş faturalar: son `horizon` günün satışları aynı ritimle ileri taşınır."""
    as_of = pd.Timestamp(as_of)
    shift = pd.Timedelta(days=horizon)
    recent = obs[obs["issue_date"] > as_of - shift].copy()
    recent["invoice_id"] = "PRJ-" + recent["invoice_id"]
    recent["issue_date"] += shift
    recent["due_date"] += shift
    recent["paid_date"] = pd.NaT
    recent["open_amount"] = recent["amount"]
    return recent


def forecast(obs: pd.DataFrame, as_of, opening: float, outflows: pd.DataFrame, horizon: int = 90,
             n_sims: int = 2000, include_projected: bool = True, seed: int = 0,
             cheques: pd.DataFrame | None = None) -> dict:
    as_of = pd.Timestamp(as_of)
    X, y = training_frame(obs, as_of)
    model = fit_model(X, y)

    obs = obs.copy()
    obs["disputed"] = obs["disputed"].fillna(False).astype(bool) if "disputed" in obs else False
    obs["promised_date"] = pd.to_datetime(obs["promised_date"]) if "promised_date" in obs else pd.NaT
    is_open = obs["open_amount"] > 0
    # İtirazlı faturalar çözülene kadar ne tahmine ne hatırlatma listesine girer.
    open_inv = obs[is_open & ~obs["disputed"]].assign(projected=False)
    parts = [open_inv]
    if include_projected:
        parts.append(project_sales(obs, as_of, horizon).assign(projected=True, disputed=False, promised_date=pd.NaT))
    target = pd.concat(parts, ignore_index=True)
    # Özellikler bugünün bilgisiyle hesaplanır; tahmin edilen faturalar geçmişe karışmaz.
    combined = pd.concat([obs[~is_open], target], ignore_index=True)
    feats = build_features(combined, ref=as_of).iloc[-len(target):].reset_index(drop=True)
    target["p_default"] = target["customer_id"].map(default_rates(obs, as_of)).to_numpy()

    # Ödeme sözü verilmiş faturada söz tarihi yeni vade sayılır; müşterinin olağan
    # gecikme alışkanlığı bu tarihe göre uygulanır (varsayım: söz de vade kadar tutulur).
    promised = target["promised_date"] > as_of
    sim_inv = target.assign(due_date=target["promised_date"].where(promised, target["due_date"]))
    sim = simulate(sim_inv, model.predict(feats), as_of, opening, outflows, horizon, n_sims, seed=seed,
                   aging=aging_curve(obs, as_of), cheques=cheques)
    real = ~target["projected"].to_numpy()
    gap_day = sim.breach_day if sim.breach_day is not None else horizon
    ranked = actions.prioritize(target[real], sim.pay_day[real], as_of, gap_day, actions.payment_habits(obs))
    return {"as_of": as_of, "model": model, "simple_model": isinstance(model, FallbackModel), "n_train": len(X),
            "sim": sim, "ranked": ranked, "gap_day": gap_day, "metrics": actions.metrics(obs, as_of),
            "opening": opening, "outflows": outflows, "obs": obs,
            "disputed_total": float(obs.loc[is_open & obs["disputed"], "open_amount"].sum())}


def backtest_model(full: pd.DataFrame, as_of, holdout_days: int = 240) -> dict:
    """Zaman bazlı ayrım: kesim tarihine kadar eğit, sonrasında kesilen olgun faturalarda ölç."""
    as_of = pd.Timestamp(as_of)
    cutoff = as_of - pd.Timedelta(days=holdout_days)
    X_tr, y_tr = training_frame(observe(full, cutoff), cutoff)
    model = DelayModel().fit(X_tr, y_tr)
    obs = observe(full, as_of)
    X, y = training_frame(obs, as_of)
    test = obs.loc[X.index, "issue_date"] > cutoff
    return evaluate(model.predict(X[test]), y[test], X.loc[test, "hist_med"])


def backtest_collections(full: pd.DataFrame, as_of, horizon: int = 90, origins: int = 6, step: int = 30,
                         n_sims: int = 1000) -> pd.DataFrame:
    """Geçmiş tarihlerde tahmin üretip, sonraki `horizon` günde gerçekleşen tahsilatla karşılaştırır."""
    as_of = pd.Timestamp(as_of)
    rows = []
    for k in range(origins):
        t = as_of - pd.Timedelta(days=horizon + k * step)
        obs = observe(full, t)
        res = forecast(obs, t, 0.0, pd.DataFrame({"date": [], "amount": []}), horizon, n_sims,
                       include_projected=False, seed=k)
        was_open = (full["issue_date"] <= t) & ~(full["true_paid_date"] <= t)
        got = was_open & (full["true_paid_date"] <= t + pd.Timedelta(days=horizon))
        actual = full.loc[got, "amount"].sum()
        lo, mid, hi = np.percentile(res["sim"].collections, [10, 50, 90])
        rows.append({"origin": t.date(), "actual": actual, "p10": lo, "p50": mid, "p90": hi,
                     "inside": lo <= actual <= hi, "err_p50_pct": (mid - actual) / actual * 100})
    return pd.DataFrame(rows)


def backtest_own(obs: pd.DataFrame, as_of, horizon: int = 90, origins: int = 4, step: int = 30,
                 min_history_days: int = 180) -> pd.DataFrame | None:
    """Kullanıcının kendi verisinde tahsilat geri testi; geçmiş yetersizse None döner.

    En eski test tarihinden önce en az `min_history_days` günlük fatura geçmişi aranır."""
    as_of = pd.Timestamp(as_of)
    span = (as_of - obs["issue_date"].min()).days
    origins = min(origins, (span - horizon - min_history_days) // step + 1)
    if origins < 1:
        return None
    full = obs.assign(true_paid_date=obs["paid_date"])
    return backtest_collections(full, as_of, horizon, origins, step)


def demo(seed: int = 7, as_of: str = "2026-10-01", **kwargs) -> dict:
    from .synthetic import generate
    full = generate(seed=seed, as_of=as_of)
    obs = observe(full, as_of)
    opening, outflows = cash_plan(obs, as_of)
    return forecast(obs, as_of, opening, outflows, **kwargs) | {"full": full}
