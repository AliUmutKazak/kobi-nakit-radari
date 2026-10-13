"""Sızıntısız özellik üretimi.

Her fatura için yalnızca referans tarihinden (varsayılan: fatura tarihi) önce
gözlenmiş ödemeler kullanılır. Az geçmişi olan müşterilerde istatistikler piyasa
ortalamasına doğru büzülür (soğuk başlangıç).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

FEATURES = ["log_amount", "amount_rel", "terms", "due_dom", "due_month", "due_dow", "market_med",
            "hist_n", "hist_med", "hist_mean", "hist_std", "hist_p90", "late_share", "last3",
            "open_cnt", "open_max_overdue"]


def _days(s: pd.Series) -> np.ndarray:
    return ((s - pd.Timestamp("2000-01-01")) / pd.Timedelta(days=1)).to_numpy(dtype=float)


def build_features(inv: pd.DataFrame, ref=None, prior_n: float = 5.0) -> pd.DataFrame:
    df = inv.reset_index(drop=True)
    issue, due, paid = _days(df["issue_date"]), _days(df["due_date"]), _days(df["paid_date"])
    ref_d = issue if ref is None else np.full(len(df), _days(pd.Series([pd.Timestamp(ref)]))[0])
    delay = paid - due
    amount = df["amount"].to_numpy(dtype=float)

    order = np.argsort(np.where(np.isnan(paid), np.inf, paid))
    n_paid = int((~np.isnan(paid)).sum())
    g_paid, g_delay = paid[order][:n_paid], delay[order][:n_paid]

    out = np.zeros((len(df), len(FEATURES)))
    market = np.zeros(len(df))
    for i in range(len(df)):
        hi = np.searchsorted(g_paid, ref_d[i])
        lo = np.searchsorted(g_paid, ref_d[i] - 90)
        window = g_delay[lo:hi] if hi - lo >= 5 else g_delay[:hi]
        market[i] = np.median(window) if len(window) else 0.0

    for idx in df.groupby("customer_id").indices.values():
        c_issue, c_due, c_paid, c_delay, c_amt = issue[idx], due[idx], paid[idx], delay[idx], amount[idx]
        for j, i in enumerate(idx):
            r = ref_d[i]
            other = np.arange(len(idx)) != j
            known = (c_paid < r) & other
            hist = c_delay[known]
            n = len(hist)
            m = market[i]
            if n:
                recent = hist[np.argsort(c_paid[known])][-3:]
                med = (n * np.median(hist) + prior_n * m) / (n + prior_n)
                mean = (n * hist.mean() + prior_n * m) / (n + prior_n)
                std, p90 = (hist.std() if n > 1 else 0.0), np.quantile(hist, 0.9)
                late, last3 = (hist > 3).mean(), recent.mean()
            else:
                med = mean = p90 = last3 = m
                std, late = 0.0, 0.5
            is_open = (c_issue < r) & ~(c_paid < r) & other
            prev_amt = c_amt[(c_issue < r) & other]
            out[i] = [np.log(amount[i]),
                      np.log(amount[i] / np.median(prev_amt)) if len(prev_amt) else 0.0,
                      due[i] - issue[i],
                      df.at[i, "due_date"].day, df.at[i, "due_date"].month, df.at[i, "due_date"].dayofweek,
                      m, n, med, mean, std, p90, late, last3,
                      is_open.sum(),
                      np.clip(r - c_due[is_open], 0, None).max() if is_open.any() else 0.0]
    return pd.DataFrame(out, columns=FEATURES, index=inv.index)
