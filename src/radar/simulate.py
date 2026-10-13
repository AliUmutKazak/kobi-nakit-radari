"""Monte Carlo likidite simülasyonu.

Üç noktada basit "vade + Gaussyen gürültü" kurgusundan ayrılır:
1. Gecikme, modelin kantillerinden kurulan çarpık bir dağılımdan çekilir.
2. Açık fatura bugüne kadar ödenmediği için dağılım "bugünden sonra" koşuluna kırpılır.
3. Faturalar bağımsız değildir: piyasa ve müşteri ortak faktörleri gecikmeleri birlikte oynatır.
4. Modelin P90'ını çoktan aşmış faturalarda model yerine geçmişten ölçülen yaşlandırma
   eğrisi kullanılır; eski alacakların büyük kısmının hiç tahsil edilemediği böyle yakalanır.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.special import ndtr

from .model import QS

P = np.array(QS)
_TAIL = np.log(0.25 / 0.10)


def _scale(q):
    return max(q[4] - q[3], 1.0) / _TAIL


def ppf(q: np.ndarray, u: np.ndarray) -> np.ndarray:
    """Kantil fonksiyonu: ortada doğrusal, altta sınırlı, üstte üstel kuyruk."""
    u = np.clip(u, 1e-9, 1 - 1e-9)
    out = np.interp(u, P, q)
    lo, hi = u < P[0], u > P[-1]
    out[lo] = q[0] - (q[1] - q[0]) * (P[0] - u[lo]) / P[0]
    out[hi] = q[4] + _scale(q) * np.log((1 - P[-1]) / (1 - u[hi]))
    return out


def cdf(q: np.ndarray, d: float) -> float:
    if d <= q[0]:
        return float(max(0.0, P[0] * (1 - (q[0] - d) / (q[1] - q[0]))))
    if d >= q[4]:
        return float(1 - (1 - P[-1]) * np.exp(-(d - q[4]) / _scale(q)))
    return float(np.interp(d, q, P))


@dataclass
class SimResult:
    dates: pd.DatetimeIndex        # gün 0 = bugün
    p10: np.ndarray
    p50: np.ndarray
    p90: np.ndarray
    prob_negative: np.ndarray      # o gün kasanın eksiye düşme olasılığı
    prob_any_breach: float         # ufuk içinde en az bir gün eksiye düşme olasılığı
    breach_day: int | None         # P10 bandının sıfırı kestiği ilk gün
    pay_day: np.ndarray            # (fatura, senaryo) ödeme günü; ufuk dışı = horizon + 1
    collections: np.ndarray        # senaryo başına mevcut açık faturalardan tahsilat


def aging_curve(inv: pd.DataFrame, as_of, max_days: int = 720) -> np.ndarray:
    """Kaplan-Meier: S[d] = vadesini d gün aşan bir faturanın hâlâ ödenmemiş olma olasılığı.

    Ödenmemiş faturalar sansürlü gözlem sayılır; erken ödenenler eğriye girmez."""
    as_of = pd.Timestamp(as_of)
    dur = (inv["paid_date"].fillna(as_of) - inv["due_date"]).dt.days.to_numpy()
    event = inv["paid_date"].notna().to_numpy()
    keep = dur >= 0
    dur, event = np.clip(dur[keep], 0, max_days), event[keep] & (dur[keep] <= max_days)
    exits = np.bincount(dur, minlength=max_days + 1)
    events = np.bincount(dur[event], minlength=max_days + 1)
    at_risk = len(dur) - np.concatenate([[0], np.cumsum(exits)[:-1]])
    return np.cumprod(1 - events / np.maximum(at_risk, 1))


def simulate(inv: pd.DataFrame, Q: np.ndarray, as_of, opening: float, outflows: pd.DataFrame,
             horizon: int = 90, n_sims: int = 2000, rho_market: float = 0.15,
             rho_customer: float = 0.35, seed: int = 0, aging: np.ndarray | None = None,
             cheques: pd.DataFrame | None = None, cheque_bounce: float = 0.034) -> SimResult:
    """inv sütunları: customer_id, issue_date, due_date, open_amount, p_default, projected.

    cheques (date, amount): portföydeki çek/senetler vade gününde kasaya girer; her biri
    `cheque_bounce` olasılıkla karşılıksız çıkar (varsayılan: TBB Risk Merkezi Ağustos 2026
    tutar bazlı oranı) ve karşılıksızlık piyasa faktörüyle birlikte artar."""
    rng = np.random.default_rng(seed)
    as_of = pd.Timestamp(as_of)
    n = len(inv)
    Q = np.sort(np.asarray(Q, float), axis=1) + np.arange(len(P)) * 1e-3
    codes, _ = pd.factorize(inv["customer_id"])
    zm = rng.standard_normal(n_sims)
    n_cust = codes.max() + 1 if n else 0
    common = np.sqrt(rho_market) * zm + np.sqrt(rho_customer) * rng.standard_normal((n_cust, n_sims))[codes]
    idio = np.sqrt(1 - rho_market - rho_customer)
    u_delay = ndtr(common + idio * rng.standard_normal((n, n_sims)))
    u_default = ndtr(-(common + idio * rng.standard_normal((n, n_sims))))

    due_off = (inv["due_date"] - as_of).dt.days.to_numpy()
    earliest = np.maximum((inv["issue_date"] - as_of).dt.days.to_numpy(), 0) + 1
    amount = inv["open_amount"].to_numpy(float)
    p_def = inv["p_default"].to_numpy(float)
    projected = inv["projected"].to_numpy(bool)

    pay_day = np.full((n, n_sims), horizon + 1, dtype=np.int32)
    inflow = np.zeros((n_sims, horizon + 1))
    collections = np.zeros(n_sims)
    sims = np.arange(n_sims)
    for i in range(n):
        d0 = -due_off[i]
        if aging is not None and d0 > Q[i, 4]:
            # Kalan ömür: S(d0)'dan itibaren koşullu eğri; eğrinin bittiği yer "tahsil edilemedi".
            target = (aging[d0] if d0 < len(aging) else 0.0) * (1 - u_delay[i])
            delay = np.searchsorted(-aging, -target)
            day = np.maximum(due_off[i] + delay, earliest[i]).astype(np.int64)
            ok = (delay < len(aging)) & (day <= horizon)
        else:
            f0 = min(cdf(Q[i], d0), 0.999)               # bugüne kadar ödenmiş olma olasılığı
            p_post = min(p_def[i] / (p_def[i] + (1 - p_def[i]) * (1 - f0)), 0.95)
            delay = ppf(Q[i], f0 + u_delay[i] * (1 - f0))
            day = np.maximum(np.ceil(due_off[i] + delay), earliest[i]).astype(np.int64)
            ok = (u_default[i] >= p_post) & (day <= horizon)
        pay_day[i, ok] = day[ok]
        np.add.at(inflow, (sims[ok], day[ok]), amount[i])
        if not projected[i]:
            collections += ok * amount[i]

    if cheques is not None and len(cheques):
        c_off = (pd.to_datetime(cheques["date"]) - as_of).dt.days.to_numpy()
        c_amt = cheques["amount"].to_numpy(float)
        z = np.sqrt(rho_market) * zm + np.sqrt(1 - rho_market) * rng.standard_normal((len(c_off), n_sims))
        cleared = ndtr(z) <= 1 - cheque_bounce
        for j in np.flatnonzero((c_off >= 1) & (c_off <= horizon)):
            inflow[cleared[j], c_off[j]] += c_amt[j]

    out = np.zeros(horizon + 1)
    off = (pd.to_datetime(outflows["date"]) - as_of).dt.days.to_numpy()
    keep = (off >= 1) & (off <= horizon)
    np.add.at(out, off[keep], outflows["amount"].to_numpy(float)[keep])
    balance = opening + np.cumsum(inflow - out, axis=1)

    p10, p50, p90 = np.percentile(balance, [10, 50, 90], axis=0)
    below = np.flatnonzero(p10 < 0)
    return SimResult(
        dates=pd.date_range(as_of, periods=horizon + 1), p10=p10, p50=p50, p90=p90,
        prob_negative=(balance < 0).mean(axis=0),
        prob_any_breach=float((balance.min(axis=1) < 0).mean()),
        breach_day=int(below[0]) if len(below) else None,
        pay_day=pay_day, collections=collections,
    )
