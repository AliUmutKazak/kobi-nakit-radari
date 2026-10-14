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
            "open_cnt", "open_max_overdue", "has_payday", "to_payday"]

MONTH_END = 31


def _days(s: pd.Series) -> np.ndarray:
    return ((s - pd.Timestamp("2000-01-01")) / pd.Timedelta(days=1)).to_numpy(dtype=float)


def payday_habit(dom: np.ndarray, to_month_end: np.ndarray, min_n: int = 6, share: float = 0.6) -> int:
    """Müşterinin sabit ödeme günü: 0 = yok, 1-28 = ayın o günü, MONTH_END = ay sonu.

    Ödemelerin en az `share` kadarı aynı günün ±1 gün çevresinde toplanıyorsa alışkanlık sayılır."""
    n = len(dom)
    if n < min_n:
        return 0
    if (to_month_end <= 1).mean() >= share:
        return MONTH_END
    counts = np.bincount(dom.astype(int), minlength=33)
    window = counts[:-2] + counts[1:-1] + counts[2:]          # window[k]: k+1. günün ±1 çevresi
    day = int(np.argmax(window)) + 1
    return day if window[day - 1] / n >= share and day <= 28 else 0


def next_payday(day: np.datetime64, habit: int) -> np.datetime64:
    """`day` tarihinde veya sonrasında gelen ilk ödeme günü."""
    month, one_month = day.astype("datetime64[M]"), np.timedelta64(1, "M")
    if habit == MONTH_END:
        return (month + one_month).astype("datetime64[D]") - np.timedelta64(1, "D")
    offset = np.timedelta64(habit - 1, "D")
    nxt = month.astype("datetime64[D]") + offset
    return nxt if nxt >= day else (month + one_month).astype("datetime64[D]") + offset


def build_features(inv: pd.DataFrame, ref=None, prior_n: float = 5.0) -> pd.DataFrame:
    df = inv.reset_index(drop=True)
    issue, due, paid = _days(df["issue_date"]), _days(df["due_date"]), _days(df["paid_date"])
    ref_d = issue if ref is None else np.full(len(df), _days(pd.Series([pd.Timestamp(ref)]))[0])
    delay = paid - due
    amount = df["amount"].to_numpy(dtype=float)
    dom = df["paid_date"].dt.day.to_numpy(dtype=float)
    to_eom = (df["paid_date"].dt.days_in_month - df["paid_date"].dt.day).to_numpy(dtype=float)
    due_np = df["due_date"].to_numpy().astype("datetime64[D]")
    due_parts = np.column_stack([df["due_date"].dt.day, df["due_date"].dt.month, df["due_date"].dt.dayofweek])

    order = np.argsort(np.where(np.isnan(paid), np.inf, paid))
    n_paid = int((~np.isnan(paid)).sum())
    g_paid, g_delay = paid[order][:n_paid], delay[order][:n_paid]

    out = np.zeros((len(df), len(FEATURES)))
    # Piyasa medyanı yalnızca referans tarihine bağlı: her farklı tarih için bir kez hesaplanır.
    dates, inverse = np.unique(ref_d, return_inverse=True)
    per_date = np.zeros(len(dates))
    for k, r in enumerate(dates):
        hi = np.searchsorted(g_paid, r)
        lo = np.searchsorted(g_paid, r - 90)
        window = g_delay[lo:hi] if hi - lo >= 5 else g_delay[:hi]
        per_date[k] = np.median(window) if len(window) else 0.0
    market = per_date[inverse]

    for idx in df.groupby("customer_id").indices.values():
        c_issue, c_due, c_paid, c_delay, c_amt = issue[idx], due[idx], paid[idx], delay[idx], amount[idx]
        c_dom, c_eom = dom[idx], to_eom[idx]
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
            habit = payday_habit(c_dom[known], c_eom[known])
            to_payday = float((next_payday(due_np[i], habit) - due_np[i]).astype(int)) if habit else 0.0
            is_open = (c_issue < r) & ~(c_paid < r) & other
            prev_amt = c_amt[(c_issue < r) & other]
            out[i] = [np.log(amount[i]),
                      np.log(amount[i] / np.median(prev_amt)) if len(prev_amt) else 0.0,
                      due[i] - issue[i], *due_parts[i],
                      m, n, med, mean, std, p90, late, last3,
                      is_open.sum(),
                      np.clip(r - c_due[is_open], 0, None).max() if is_open.any() else 0.0,
                      float(habit > 0), to_payday]
    return pd.DataFrame(out, columns=FEATURES, index=inv.index)
