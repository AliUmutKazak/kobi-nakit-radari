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
from scipy.optimize import minimize
from scipy.special import log_ndtr, ndtr, ndtri

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
    min_balance: np.ndarray        # senaryo başına ufuk içindeki en düşük kasa
    breach_day: int | None         # P10 bandının sıfırı kestiği ilk gün
    pay_day: np.ndarray            # (fatura, senaryo) ödeme günü; ufuk dışı = horizon + 1
    collections: np.ndarray        # senaryo başına mevcut açık faturalardan tahsilat
    paths: np.ndarray | None = None  # (senaryo, gün) kasa yolları: "şu fatura gelmezse" hesapları için


PRIOR_RHO = (0.15, 0.35)
CHEQUE_BOUNCE = 0.034     # TBB Risk Merkezi, Ağustos 2026, tutar bazında karşılıksız çek oranı
RECAL_GRID = np.linspace(0.0, 1.0, 101)


def pit_recalibration(z: np.ndarray, censored: np.ndarray, shrink_n: float = 200.0) -> np.ndarray:
    """Koşullu tahmin dağılımının parametresiz yeniden ayarı (Kuleshov vd. 2018, "calibrated regression").

    Geçmiş tahminlerde gerçekleşenin dağılımdaki yeri (PIT, 0-1) tahmin doğruysa tekdüze dağılır. Gerçek PIT
    dağılımı Kaplan-Meier ile (ödenmemiş fatura sağdan sansürlü) çıkarılır; simülasyonda tekdüze sayı bu
    dağılımın kantiline çevrilir. Az gözlemde birim dönüşüme doğru büzülür. Dönen dizi RECAL_GRID üzerindeki
    kantillerdir."""
    u = np.clip(ndtr(np.asarray(z, float)), 0.0, 1.0)
    event = ~np.asarray(censored, bool)
    order = np.argsort(u, kind="stable")
    u, event = u[order], event[order]
    n = len(u)
    at_risk = n - np.arange(n)
    surv = np.cumprod(1 - event / at_risk)            # S(u_i) adım adım
    cdf_vals = 1 - surv
    top = cdf_vals[-1] if n else 0.0
    q = np.empty_like(RECAL_GRID)
    for j, v in enumerate(RECAL_GRID):
        if v <= top and n:
            q[j] = u[np.searchsorted(cdf_vals, v, side="left").clip(0, n - 1)]
        else:                                          # gözlenen en büyük PIT'in üstündeki kütle: doğrusal olarak 1'e
            last = u[-1] if n else 0.0
            q[j] = last + (1 - last) * ((v - top) / (1 - top) if top < 1 else 1.0)
    q[0], q[-1] = 0.0, 1.0
    q = np.maximum.accumulate(q)
    w = n / (n + shrink_n)
    return w * q + (1 - w) * RECAL_GRID      # veri yetersizken kullanılan piyasa ve müşteri korelasyonu (varsayım)


def _between_share(z: np.ndarray, groups: np.ndarray) -> tuple[float, int]:
    """Tek yönlü rastgele etkiler ANOVA'sı: grup etkisinin toplam varyanstaki payı ve grup sayısı."""
    frame = pd.DataFrame({"z": z, "g": groups})
    stats = frame.groupby("g")["z"].agg(["mean", "size"])
    n, k = len(frame), len(stats)
    if k < 2 or n <= k:
        return 0.0, k
    msb = (stats["size"] * (stats["mean"] - z.mean()) ** 2).sum() / (k - 1)
    msw = ((frame["z"] - frame["g"].map(stats["mean"])) ** 2).sum() / (n - k)
    n0 = (n - (stats["size"] ** 2).sum() / n) / (k - 1)
    between = max((msb - msw) / n0, 0.0)
    return float(between / (between + msw)) if between + msw > 0 else 0.0, k


def normal_scores(Q: np.ndarray, y) -> np.ndarray:
    """Gerçekleşen gecikmenin tahmin dağılımındaki yerini (0-1) normal skora çevirir.

    Tahmin kusursuzsa skorlar standart normal dağılır: ortalaması 0, sapması 1."""
    y = np.asarray(y, float)
    Q = np.sort(np.asarray(Q, float), axis=1) + np.arange(len(P)) * 1e-3
    u = np.array([cdf(Q[i], y[i]) for i in range(len(y))])
    return ndtri(np.clip(u, 0.01, 0.99))


def conditional_scores(Q: np.ndarray, y, d0, aging: np.ndarray | None = None) -> np.ndarray:
    """`normal_scores`un açık faturalar için karşılığı: fatura tahmin gününde `d0` gün gecikmiş ve
    hâlâ ödenmemişken, gerçekleşen gecikmenin koşullu dağılımdaki yeri. Simülasyonla aynı kuralı
    izler: modelin P90'ını aşmış faturalarda yaşlandırma eğrisi kullanılır."""
    y, d0 = np.asarray(y, float), np.asarray(d0, float)
    Q = np.sort(np.asarray(Q, float), axis=1) + np.arange(len(P)) * 1e-3
    u = np.empty(len(y))
    for i in range(len(y)):
        if aging is not None and d0[i] > Q[i, 4]:
            last = len(aging) - 1
            s0 = aging[int(min(d0[i], last))]
            u[i] = 1 - aging[int(min(y[i], last))] / s0 if s0 > 0 else 0.5
        else:
            f0 = min(cdf(Q[i], d0[i]), 0.999)
            u[i] = (cdf(Q[i], y[i]) - f0) / (1 - f0)
    return ndtri(np.clip(u, 0.01, 0.99))


def censored_normal_fit(z: np.ndarray, censored: np.ndarray) -> tuple[float, float]:
    """Sağdan sansürlü normal örneklemin ortalaması ve sapması (en çok olabilirlik).

    Hâlâ ödenmemiş bir faturanın skoru yalnızca alt sınırdır; bunu gerçek değer saymak
    ortalamayı aşağı çeker ve iyimserliği gizler."""
    z, censored = np.asarray(z, float), np.asarray(censored, bool)
    if not censored.any():
        return float(z.mean()), float(z.std())

    def nll(params):
        mu, sigma = params[0], np.exp(params[1])
        r = (z - mu) / sigma
        return -(np.sum(-0.5 * r[~censored] ** 2 - np.log(sigma)) + np.sum(log_ndtr(-r[censored])))

    fit = minimize(nll, [z.mean(), np.log(max(z.std(), 0.3))], method="Nelder-Mead")
    return float(fit.x[0]), float(np.exp(fit.x[1]))


def correlation_from_scores(z: np.ndarray, market_group, customer_id, prior_groups: float = 4.0) -> tuple[float, float]:
    """Skorlardaki ortak hareketi piyasa (grup) ve müşteri (grup içi) paylarına ayırır."""
    market_group = np.asarray(market_group, str)
    rho_m, k = _between_share(z, market_group)
    rho_m = (k * rho_m + prior_groups * PRIOR_RHO[0]) / (k + prior_groups)
    centered = z - pd.Series(z).groupby(market_group).transform("mean").to_numpy()
    rho_c, _ = _between_share(centered, np.char.add(np.asarray(customer_id, str), market_group))
    rho_c *= 1 - rho_m                     # müşteri payı, piyasa etkisi çıkarıldıktan sonra kalan varyans üzerinden
    return float(min(rho_m, 0.5)), float(min(rho_c, 0.6))


def estimate_correlation(Q: np.ndarray, y, customer_id, due_date, min_rows: int = 200,
                         prior_groups: float = 4.0) -> tuple[float, float]:
    """Gecikmelerin birlikte hareketini şirketin kendi geçmişinden ölçer.

    Her faturanın gerçekleşen gecikmesi, tahmin dağılımındaki yerine (0-1) ve oradan normal
    skora çevrilir. Aynı çeyrekteki faturaların ortak sapması piyasa etkisi, aynı müşterinin
    aynı çeyrekteki ortak sapması müşteri etkisidir; simülasyondaki faktörler de 90 günlük
    ufuk boyunca sabit kaldığı için gruplar çeyrek bazındadır. Çeyrek sayısı az olduğundan
    piyasa tahmini ön değere doğru büzülür."""
    if len(np.asarray(y)) < min_rows:
        return PRIOR_RHO
    quarter = pd.PeriodIndex(pd.to_datetime(due_date), freq="Q").astype(str).to_numpy()
    return correlation_from_scores(normal_scores(Q, y), quarter, customer_id, prior_groups)


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


def snap_to_payday(day: np.ndarray, habit: int, as_of, earliest: int) -> np.ndarray:
    """Gün ofsetlerini (as_of'a göre) müşterinin en yakın ödeme gününe taşır; `earliest`ten önceye gitmez.

    En yakın güne yuvarlamak ortalama gecikmeyi korur (model gecikmeyi zaten ödeme günlerine oturmuş
    geçmişten öğrenir; "bir sonraki ödeme günü"ne itmek her ödemeyi ortalama yarım dönem geciktirirdi) ve
    ödemeleri takvimde doğru yere toplar: ay sonu ödeyen müşterinin parası ayın 1'inden önce gelir ya da gelmez."""
    base = np.datetime64(pd.Timestamp(as_of).date(), "D")
    dates = base + np.asarray(day, dtype="int64").astype("timedelta64[D]")
    month = dates.astype("datetime64[M]")
    one = np.timedelta64(1, "M")
    if habit >= 31:
        nxt = (month + one).astype("datetime64[D]") - np.timedelta64(1, "D")
        prev = month.astype("datetime64[D]") - np.timedelta64(1, "D")
        prev = np.where(nxt == dates, dates, prev)
    else:
        off = np.timedelta64(habit - 1, "D")
        this = month.astype("datetime64[D]") + off
        nxt = np.where(this >= dates, this, (month + one).astype("datetime64[D]") + off)
        prev = np.where(this <= dates, this, (month - one).astype("datetime64[D]") + off)
    pick = np.where((dates - prev) <= (nxt - dates), prev, nxt)
    out = (pick - base).astype(int)
    return np.where(out < earliest, (nxt - base).astype(int), out)


def simulate(inv: pd.DataFrame, Q: np.ndarray, as_of, opening: float, outflows: pd.DataFrame,
             horizon: int = 90, n_sims: int = 2000, rho_market: float = 0.15,
             rho_customer: float = 0.35, seed: int = 0, aging: np.ndarray | None = None,
             cheques: pd.DataFrame | None = None, cheque_bounce: float = CHEQUE_BOUNCE,
             z_shift: float = 0.0, z_scale: float = 1.0, widen: float = 1.0,
             recal: np.ndarray | None = None, sales_level: np.ndarray | None = None,
             cheque_p: np.ndarray | None = None, cheque_terms: np.ndarray | None = None,
             cheque_by_customer: bool = False, lag: int = 0, payday: np.ndarray | None = None) -> SimResult:
    """inv sütunları: customer_id, issue_date, due_date, open_amount, p_default, projected.

    payday: fatura başına müşterinin ödeme günü alışkanlığı (0 = yok, 1-28 = ayın günü, 31 = ay sonu; bkz.
    features.payday_habit). Verilirse simüle edilen ödeme günü en yakın ödeme gününe oturtulur (snap_to_payday).

    lag: tahsilat kayıtları `as_of`'tan bu kadar gün geride (ör. muhasebe tahsilatları geç işliyor). Faturaların
    açık olduğu yalnızca kayıtların son günü için bilinir; o günden sonra ödenmiş olabilirler. Arada (as_of'tan
    önce) gelen paralar bugünkü kasa bakiyesinin içindedir: gelecek tahsilata ikinci kez eklenmez.

    cheque_p / cheque_terms: fatura kapandığında ödemenin çekle yapılma olasılığı ve senaryo başına çek vadesi
    (gün; bkz. pipeline.cheque_habits). Çekle kapanan faturanın parası vadede gelir ve çek portföydeki çekler
    gibi karşılıksız çıkabilir. pay_day paranın kasaya girdiği gündür; collections kapanan faturalardır.

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
    # z_shift / z_scale: geçmişteki ileriye dönük tahminlerin sistematik hatası (bkz. pipeline.calibrate).
    # Fatura başına ayrı değer de verilebilir (vadesi geçmiş ve geçmemiş faturalar ayrı kalibre edilir).
    z_shift, z_scale = (np.broadcast_to(np.asarray(v, float), (n,))[:, None] for v in (z_shift, z_scale))
    u_delay = ndtr(z_shift + z_scale * (common + idio * rng.standard_normal((n, n_sims))))
    u_default = ndtr(-(common + idio * rng.standard_normal((n, n_sims))))

    due_off = (inv["due_date"] - as_of).dt.days.to_numpy()
    earliest = np.maximum((inv["issue_date"] - as_of).dt.days.to_numpy(), -lag) + 1
    amount = inv["open_amount"].to_numpy(float)
    p_def = inv["p_default"].to_numpy(float)
    projected = inv["projected"].to_numpy(bool)

    if cheque_p is not None:
        # Ayrı rastgele akış: çek ayarı olmadan sonuçlar eskisiyle birebir aynı kalır.
        rng_c = np.random.default_rng(seed + 31)
        # Çekle ödeme fatura başına çekilir. Müşteri başına çekmek (müşteri bir senaryoda ya hep çekle ya hep
        # havaleyle öder) laboratuvarda denendi ve reddedildi: bandı gereğinden geniş yaptı, aralık skoru
        # kötüleşti (LAB_RAPORU.md, 17 Ekim 2026). Seçenek deneyin tekrarlanabilmesi için duruyor.
        u = rng_c.random((n_cust, n_sims))[codes] if cheque_by_customer else rng_c.random((n, n_sims))
        by_cheque = u < np.asarray(cheque_p, float)[:, None]
        zc = np.sqrt(rho_market) * zm + np.sqrt(1 - rho_market) * rng_c.standard_normal((n, n_sims))
        bounced = by_cheque & (ndtr(zc) > 1 - cheque_bounce)
    pay_day = np.full((n, n_sims), horizon + 1, dtype=np.int32)
    inflow = np.zeros((n_sims, horizon + 1))
    collections = np.zeros(n_sims)
    sims = np.arange(n_sims)
    for i in range(n):
        d0 = -due_off[i] - lag                            # kayıtların son günündeki vade aşımı
        if aging is not None and d0 > Q[i, 4]:
            # Kalan ömür: S(d0)'dan itibaren koşullu eğri; eğrinin bittiği yer "tahsil edilemedi".
            ui = np.interp(u_delay[i], RECAL_GRID, recal[i]) if recal is not None else u_delay[i]
            target = (aging[d0] if 0 <= d0 < len(aging) else float(d0 < 0)) * (1 - ui)
            delay = np.searchsorted(-aging, -target)
            day = np.maximum(due_off[i] + delay, earliest[i]).astype(np.int64)
            ok = (delay < len(aging)) & (day <= horizon)
        else:
            f0 = min(cdf(Q[i], d0), 0.999)               # bugüne kadar ödenmiş olma olasılığı
            p_post = min(p_def[i] / (p_def[i] + (1 - p_def[i]) * (1 - f0)), 0.95)
            ui = np.interp(u_delay[i], RECAL_GRID, recal[i]) if recal is not None else u_delay[i]
            delay = ppf(Q[i], f0 + ui * (1 - f0))
            # En yakın güne yuvarlama: model tam gün gecikmelerden öğrenir; yukarı yuvarlamak her ödemeye
            # ortalama yarım gün gecikme ekliyor ve kısa ufukta tahsilatı sistematik düşük gösteriyordu.
            day = np.maximum(np.floor(due_off[i] + delay + 0.5), earliest[i]).astype(np.int64)
            ok = (u_default[i] >= p_post) & (day <= horizon)
        if payday is not None and payday[i]:
            day = snap_to_payday(day, int(payday[i]), as_of, earliest[i])
            ok = ok & (day <= horizon)
        closed = ok & (day >= 1)                          # day < 1: kayıtların son günüyle bugün arasında ödendi
        if cheque_p is not None and cheque_p[i] > 0:
            day = np.where(by_cheque[i], day + cheque_terms[i], day)
            ok = ok & ~bounced[i] & (day <= horizon)
        ok = ok & (day >= 1)
        pay_day[i, ok] = day[ok]
        if projected[i]:
            # Gelecek satışların kendisi de belirsizdir. `sales_level` verilmişse (işletmenin geçmiş satış tahmini
            # hatalarından, bkz. pipeline.sales_errors) senaryo başına ortak bir düzey katsayısı uygulanır; yoksa
            # faturalar Poisson(1) ağırlığıyla yeniden örneklenir (gerçek KOBİ verisinde bu tek başına fazla dardı).
            if sales_level is not None:
                block = int(inv["sales_block"].iloc[i]) if "sales_block" in inv else 0
                weight = sales_level[min(block, len(sales_level) - 1)]
            else:
                weight = rng.poisson(1.0, n_sims)
            np.add.at(inflow, (sims[ok], day[ok]), amount[i] * weight[ok])
        else:
            np.add.at(inflow, (sims[ok], day[ok]), amount[i])
            collections += closed * amount[i]

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
    w_lo, w_hi = (widen, widen) if np.isscalar(widen) else widen
    if (w_lo, w_hi) != (1.0, 1.0):
        # Toplam düzeyde genişletme: medyanın altı (kötümser taraf) ve üstü ayrı katsayıyla ölçeklenir.
        med = np.median(balance, axis=0)
        dev = balance - med
        balance = med + np.where(dev < 0, w_lo * dev, w_hi * dev)
        cmed = np.median(collections)
        cdev = collections - cmed
        collections = cmed + np.where(cdev < 0, w_lo * cdev, w_hi * cdev)

    p10, p50, p90 = np.percentile(balance, [10, 50, 90], axis=0)
    below = np.flatnonzero(p10 < 0)
    return SimResult(
        dates=pd.date_range(as_of, periods=horizon + 1), p10=p10, p50=p50, p90=p90,
        prob_negative=(balance < 0).mean(axis=0),
        prob_any_breach=float((balance.min(axis=1) < 0).mean()), min_balance=balance.min(axis=1),
        breach_day=int(below[0]) if len(below) else None,
        pay_day=pay_day, collections=collections, paths=balance,
    )
