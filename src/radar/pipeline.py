"""Uçtan uca akış: veri -> model -> simülasyon -> öncelikli tahsilat listesi, ve geri testler."""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import actions
from .features import build_features
from .model import DelayModel, FallbackModel, evaluate, fit_model, training_frame
from .simulate import (PRIOR_RHO, aging_curve, censored_normal_fit, conditional_scores, correlation_from_scores,
                       simulate)
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


def censor(obs: pd.DataFrame, t) -> pd.DataFrame:
    """Tablonun `t` tarihinde görünen hâli: sonraki faturalar ve ödemeler gizlenir."""
    t = pd.Timestamp(t)
    df = obs[obs["issue_date"] <= t].copy()
    df["paid_date"] = df["paid_date"].where(df["paid_date"] <= t)
    df["open_amount"] = np.where(df["paid_date"].isna(), df["amount"], 0.0)
    return df.reset_index(drop=True)


def calibrate(obs: pd.DataFrame, as_of, origins: int = 4, step: int = 90, mature_days: int = 60,
              min_scores: int = 100, shrink_n: float = 200.0) -> dict:
    """Simülasyonun belirsizlik ayarlarını, geçmişteki ileriye dönük tahminlerin hatasından çıkarır.

    Son `origins` çeyreğin her birinin başına dönülür, o günkü bilgiyle model kurulur ve o gün
    açık olan faturaların gecikmesi tahmin edilir. Gerçekleşenle karşılaştırınca:
    - skorların ortalaması sıfırdan sapıyorsa model sistematik olarak geç ya da erken tahmin
      ediyordur (ör. gecikmeler uzarken geride kalır) -> kayma,
    - sapması 1'den büyükse aralıklar dardır -> ölçek,
    - çeyrekler arası ve müşteriler arası ortak hareket -> korelasyonlar.
    Kayma ve ölçek, vadesi gelmemiş ("fresh") ve vadesi geçmiş ("overdue") faturalar için ayrı
    ölçülür; ikincisinde tahmin koşullu kuyruğa dayanır ve hatası farklıdır.
    Modelin kendi eğitim verisindeki uyumu bunları ölçemez; o veri bilinen geçmiştir."""
    as_of = pd.Timestamp(as_of)
    neutral = {"z_shift": 0.0, "z_scale": 1.0, "n": 0}
    default = {"rho_market": PRIOR_RHO[0], "rho_customer": PRIOR_RHO[1], "fresh": neutral, "overdue": neutral}
    final = obs.set_index("invoice_id")
    parts = []
    for k in range(1, origins + 1):
        t = as_of - pd.Timedelta(days=k * step)
        past = censor(obs, t)
        if not len(past):
            break
        X, y = training_frame(past, t)
        if len(X) < 60:
            break
        # Sonucu seçim yanlılığı olmadan bilinenler: o gün açık ve bugün itibarıyla olgunlaşmış faturalar.
        test = past[past["paid_date"].isna() & (past["due_date"] <= as_of - pd.Timedelta(days=mature_days))]
        if "disputed" in test:
            test = test[~test["disputed"].fillna(False).astype(bool)]
        if len(test) < 10:
            continue
        outcome = final.loc[test["invoice_id"]]
        delay = (outcome["paid_date"].fillna(as_of) - outcome["due_date"]).dt.days.to_numpy()
        d0 = (t - test["due_date"]).dt.days.to_numpy()
        Q = fit_model(X, y).predict(build_features(past, ref=t).loc[test.index])
        parts.append(pd.DataFrame({"z": conditional_scores(Q, delay, d0, aging_curve(past, t)), "origin": str(k),
                                   "customer_id": test["customer_id"].to_numpy(), "overdue": d0 > 0,
                                   "censored": outcome["paid_date"].isna().to_numpy()}))
    if not parts:
        return default
    scores = pd.concat(parts, ignore_index=True)
    if len(scores) < min_scores:
        return default

    def group(part: pd.DataFrame) -> dict:
        n = len(part)
        if n < 30:
            return neutral | {"n": n}
        mu, sigma = censored_normal_fit(part["z"].to_numpy(), part["censored"].to_numpy())
        w = n / (n + shrink_n)                               # az gözlemde düzeltme sıfıra / bire büzülür
        return {"z_shift": float(w * np.clip(mu, -1, 1)), "z_scale": float(1 + w * (np.clip(sigma, 0.7, 1.6) - 1)), "n": n}

    rho_m, rho_c = correlation_from_scores(scores["z"].to_numpy(), scores["origin"], scores["customer_id"])
    return {"rho_market": rho_m, "rho_customer": rho_c,
            "fresh": group(scores[~scores["overdue"]]), "overdue": group(scores[scores["overdue"]])}


def forecast(obs: pd.DataFrame, as_of, opening: float, outflows: pd.DataFrame, horizon: int = 90,
             n_sims: int = 2000, include_projected: bool = True, seed: int = 0,
             cheques: pd.DataFrame | None = None, calib_hook=None) -> dict:
    """calib_hook: kalibrasyon sözlüğünü değiştiren isteğe bağlı fonksiyon (yalnızca deneyler için)."""
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
    calib = calibrate(obs, as_of)
    if calib_hook is not None:
        calib = calib_hook(calib)
    ctx = {"sim_inv": sim_inv, "Q": model.predict(feats), "aging": aging_curve(obs, as_of), "cheques": cheques,
           "horizon": horizon, "n_sims": n_sims, "seed": seed, "calib": calib}
    sim = simulate(sim_inv, ctx["Q"], as_of, opening, outflows, horizon, n_sims, seed=seed, aging=ctx["aging"],
                   cheques=cheques, **_sim_args(calib, sim_inv, as_of))
    real = ~target["projected"].to_numpy()
    gap_day = sim.breach_day if sim.breach_day is not None else horizon
    ranked = actions.prioritize(target[real], sim.pay_day[real], as_of, gap_day, actions.payment_habits(obs), horizon)
    return {"as_of": as_of, "model": model, "simple_model": isinstance(model, FallbackModel), "n_train": len(X),
            "sim": sim, "ranked": ranked, "gap_day": gap_day, "metrics": actions.metrics(obs, as_of),
            "opening": opening, "outflows": outflows, "obs": obs, "ctx": ctx,
            "disputed_total": float(obs.loc[is_open & obs["disputed"], "open_amount"].sum())}


def _sim_args(calib: dict, inv: pd.DataFrame, as_of) -> dict:
    overdue = (inv["due_date"] < pd.Timestamp(as_of)).to_numpy() & ~inv["projected"].to_numpy()
    pick = lambda key: np.where(overdue, calib["overdue"][key], calib["fresh"][key])
    return {"rho_market": calib["rho_market"], "rho_customer": calib["rho_customer"],
            "z_shift": pick("z_shift"), "z_scale": pick("z_scale")}


def scenario(res: dict, collect_ids=(), collect_in_days: int = 7, delay_labels=(), delay_days: int = 0):
    """Aynı rastgele senaryolarla "şu olsaydı" hesabı.

    collect_ids: bu faturalar `collect_in_days` gün içinde kesin tahsil edilmiş sayılır.
    delay_labels / delay_days: bu gider kalemleri o kadar gün ertelenir (ufkun dışına çıkan düşer)."""
    ctx, as_of = res["ctx"], res["as_of"]
    inv = ctx["sim_inv"].copy()
    hit = inv["invoice_id"].isin(list(collect_ids)) & ~inv["projected"]
    cash = float(inv.loc[hit, "open_amount"].sum())
    inv.loc[hit, "open_amount"] = 0.0          # satır yerinde kalır ki rastgele sayılar kaymasın
    out = res["outflows"].copy()
    if delay_days and len(out) and "label" in out:
        late = out["label"].isin(list(delay_labels))
        out.loc[late, "date"] = pd.to_datetime(out.loc[late, "date"]) + pd.Timedelta(days=delay_days)
    if cash:
        out = pd.concat([out, pd.DataFrame({"date": [as_of + pd.Timedelta(days=collect_in_days)],
                                            "amount": [-cash], "label": ["Tahsilat (senaryo)"]})], ignore_index=True)
    return simulate(inv, ctx["Q"], as_of, res["opening"], out, ctx["horizon"], ctx["n_sims"],
                    seed=ctx["seed"], **_sim_args(ctx["calib"], inv, as_of),
                    aging=ctx["aging"], cheques=ctx["cheques"])


def gap_summary(res: dict, max_k: int = 40, collect_in_days: int = 7) -> dict:
    """Kötümser senaryodaki açığın derinliği ve onu kapatmak için listeden kaç fatura gerektiği.

    k = None: listedeki ilk `max_k` faturanın tamamı tahsil edilse de açık kapanmıyor."""
    sim = res["sim"]
    out = {"gap": float(max(0.0, -sim.p10.min())), "gap_day": int(sim.p10.argmin()), "k": 0, "amount": 0.0}
    if sim.breach_day is None:
        return out
    todo = res["ranked"][res["ranked"]["actionable"]].head(max_k)
    ids = list(todo["invoice_id"])
    closes = lambda k: scenario(res, ids[:k], collect_in_days).breach_day is None
    if not ids or not closes(len(ids)):
        return out | {"k": None, "amount": float(todo["open_amount"].sum())}
    lo, hi = 1, len(ids)                       # daha çok tahsilat hiçbir zaman zarar vermez: ikili arama güvenli
    while lo < hi:
        mid = (lo + hi) // 2
        lo, hi = (lo, mid) if closes(mid) else (mid + 1, hi)
    return out | {"k": lo, "amount": float(todo["open_amount"].head(lo).sum())}


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
