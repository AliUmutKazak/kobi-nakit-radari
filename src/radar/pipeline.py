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
    return df                                   # satır numaraları korunur: önceden hesaplanmış özelliklerle eşleşir


def calibrate(obs: pd.DataFrame, as_of, origins: int = 4, step: int = 90, mature_days: int = 60,
              min_scores: int = 100, shrink_n: float = 200.0, feats: pd.DataFrame | None = None) -> dict:
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
    feats = build_features(obs) if feats is None else feats
    parts = []
    for k in range(1, origins + 1):
        t = as_of - pd.Timedelta(days=k * step)
        past = censor(obs, t)
        if not len(past):
            break
        X, y = training_frame(past, t, feats=feats)
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
    feats_issue = build_features(obs)
    X, y = training_frame(obs, as_of, feats=feats_issue)
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
    calib = calibrate(obs, as_of, feats=feats_issue)
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
            "info": {"n_invoices": int(len(obs)), "n_train": int(len(X)), "n_customers": int(obs["customer_id"].nunique()),
                     "history_from": obs["issue_date"].min(), "simple_model": isinstance(model, FallbackModel),
                     "n_calibration": int(calib["fresh"]["n"] + calib["overdue"]["n"]),
                     "rho_market": calib["rho_market"], "rho_customer": calib["rho_customer"]},
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


def _p10_min(paths: np.ndarray) -> float:
    return float(np.percentile(paths.min(axis=1), 10))


def invoice_impact(res: dict, invoice_ids) -> pd.Series:
    """Her fatura için: ufuk içinde hiç gelmezse kötümser (P10) en düşük kasa kaç TL düşer.

    Aynı senaryo yolları kullanılır; yalnızca o faturanın girişi çıkarılır. Önceliğin nedenini sayıyla
    gösterir: büyük ama zaten geç gelmesi beklenen bir fatura, küçük ama açığın olduğu haftada gelecek
    bir faturadan daha az etkili olabilir."""
    sim, inv = res["sim"], res["ctx"]["sim_inv"]
    if sim.paths is None:
        return pd.Series(dtype=float)
    base = _p10_min(sim.paths)
    days = np.arange(sim.paths.shape[1])
    rows = {str(i): k for k, i in enumerate(inv["invoice_id"].astype(str)) if not inv["projected"].iloc[k]}
    out = {}
    for i in map(str, invoice_ids):
        k = rows.get(i)
        if k is None:
            continue
        arrived = days[None, :] >= sim.pay_day[k][:, None]          # senaryo × gün: para gelmiş mi
        out[i] = base - _p10_min(sim.paths - inv["open_amount"].iloc[k] * arrived)
    return pd.Series(out, dtype=float)


def customer_delay(res: dict, customer_ids, days: int) -> dict:
    """Seçilen müşterilerin bugün açık faturaları `days` gün daha geç gelirse kasa bandı (aynı senaryolar).

    Ortak şok ve alacak yoğunlaşması sorusu: "en büyük müşterim bir ay geç öderse kasam ne olur?".
    Gelecek satışlar senaryoya dahil değildir (yalnızca bugün açık faturalar kayar)."""
    sim, inv = res["sim"], res["ctx"]["sim_inv"]
    hit = np.flatnonzero(inv["customer_id"].isin(list(customer_ids)).to_numpy() & ~inv["projected"].to_numpy())
    paths = sim.paths.copy()
    t = np.arange(paths.shape[1])[None, :]
    for k in hit:
        amount = float(inv["open_amount"].iloc[k])
        pd_k = sim.pay_day[k][:, None]
        paths -= amount * (t >= pd_k)                    # eski ödeme günü
        paths += amount * (t >= pd_k + days)             # yeni ödeme günü (ufkun dışına çıkan düşer)
    p10, p50, p90 = np.percentile(paths, [10, 50, 90], axis=0)
    return {"p10": p10, "p50": p50, "p90": p90, "amount": float(inv["open_amount"].iloc[hit].sum()),
            "prob_any_breach": float((paths.min(axis=1) < 0).mean()), "p10_min": _p10_min(paths),
            "p10_min_before": _p10_min(sim.paths)}


def fx_exposure(res: dict) -> pd.DataFrame:
    """Bugün açık dövizli alacak: para birimi, orijinal tutar, girilen kur ve TL karşılığı."""
    obs = res["obs"]
    if "currency" not in obs:
        return pd.DataFrame()
    fx = obs[(obs["open_amount"] > 0) & (obs["currency"].fillna("TRY") != "TRY")]
    if fx.empty:
        return pd.DataFrame()
    rate = fx["fx_rate"] if "fx_rate" in fx else pd.Series(np.nan, index=fx.index)
    return (fx.assign(original=fx["open_amount"] / rate, rate=rate)
            .groupby("currency").agg(original=("original", "sum"), rate=("rate", "first"), tl=("open_amount", "sum"))
            .reset_index())


def fx_shift(res: dict, pct: float) -> dict:
    """TL, dövizlere karşı `pct` kadar değer kaybederse (eksi: kazanırsa) bugün açık dövizli faturalardan gelecek
    TL tutarı o oranda değişir; aynı senaryolarla kasa bandı. Kur tahmini değil, kullanıcının senaryosudur.
    Dövizli borçlar (ödenecekler) dosyada TL olduğundan kapsam dışıdır."""
    sim, inv = res["sim"], res["ctx"]["sim_inv"]
    currency = inv["currency"].fillna("TRY") if "currency" in inv else pd.Series("TRY", index=inv.index)
    hit = np.flatnonzero((currency != "TRY").to_numpy() & ~inv["projected"].to_numpy())
    paths = sim.paths.copy()
    t = np.arange(paths.shape[1])[None, :]
    for k in hit:
        paths += float(inv["open_amount"].iloc[k]) * pct * (t >= sim.pay_day[k][:, None])
    p10, p50, p90 = np.percentile(paths, [10, 50, 90], axis=0)
    return {"p10": p10, "p50": p50, "p90": p90, "prob_any_breach": float((paths.min(axis=1) < 0).mean()),
            "p10_min": _p10_min(paths), "p10_min_before": _p10_min(sim.paths)}


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


def weekly_table(res: dict, weeks: int = 13) -> pd.DataFrame:
    """13 haftalık haftalık plan. Bilinen kalemler (giderler, borçlar) ile tahmine dayananlar
    (açık faturalardan ve henüz kesilmemiş satışlardan beklenen tahsilat) ayrı sütunlardadır."""
    sim, ctx, as_of = res["sim"], res["ctx"], res["as_of"]
    inv = ctx["sim_inv"]
    amount = inv["open_amount"].to_numpy(float)
    projected = inv["projected"].to_numpy(bool)
    out = res["outflows"]
    out_off = (pd.to_datetime(out["date"]) - as_of).dt.days.to_numpy() if len(out) else np.array([])
    out_amt = out["amount"].to_numpy(float) if len(out) else np.array([])
    cheques = ctx.get("cheques")
    rows = []
    for w in range(weeks):
        lo, hi = 7 * w + 1, min(7 * (w + 1), len(sim.p50) - 1)
        if lo > hi:
            break
        in_week = ((sim.pay_day >= lo) & (sim.pay_day <= hi)).mean(axis=1) * amount
        chq = 0.0
        if cheques is not None and len(cheques):
            c_off = (pd.to_datetime(cheques["date"]) - as_of).dt.days.to_numpy()
            chq = float(cheques["amount"].to_numpy(float)[(c_off >= lo) & (c_off <= hi)].sum() * (1 - 0.034))
        rows.append({"Hafta": f"{(as_of + pd.Timedelta(days=lo)):%d.%m} – {(as_of + pd.Timedelta(days=hi)):%d.%m}",
                     "Açık faturalardan beklenen (TL)": float(in_week[~projected].sum()) + chq,
                     "Yeni satışlardan beklenen (TL)": float(in_week[projected].sum()),
                     "Bilinen çıkışlar (TL)": float(out_amt[(out_off >= lo) & (out_off <= hi)].sum()),
                     "Hafta sonu kasa, orta (P50) (TL)": float(sim.p50[hi]),
                     "Hafta sonu kasa, kötümser (TL)": float(sim.p10[hi]),
                     "Eksiye düşme olasılığı": float(sim.prob_negative[lo:hi + 1].max())})
    return pd.DataFrame(rows)


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


def naive_collections(obs: pd.DataFrame, book: pd.DataFrame, as_of, end) -> dict:
    """Üç basit yöntemle `as_of`tan `end`e kadar `book` (o gün açık faturalar) içinden tahsil edilecek tutar.

    vade: vadesi `end`e kadar gelen (ya da geçmiş) her fatura ödenir. medyan: her fatura, müşterinin `obs`taki
    geçmiş gecikme medyanı kadar geç ödenir (geçmişi olmayan müşteride genel medyan). oran: aynı uzunluktaki
    bir önceki dönemde, dönem başında açık olan alacağın yüzde kaçı tahsil edildiyse bugün de o kadarı
    tahsil edilir (muhasebede yaygın "tahsilat oranı" yaklaşımı). İlk iki yöntem vadesi çoktan geçmiş
    faturaları "yakında ödenir" sayar; şüpheli alacağı çok olan işletmede oran yöntemi en güçlü rakiptir."""
    as_of, end = pd.Timestamp(as_of), pd.Timestamp(end)
    prev = as_of - (end - as_of)
    before = obs[(obs["issue_date"] <= prev) & ~(obs["paid_date"] <= prev)]
    base = before["amount"].sum()
    rate = before.loc[before["paid_date"] <= as_of, "amount"].sum() / base if base > 0 else float("nan")
    paid = obs.dropna(subset=["paid_date"])
    lateness = (paid["paid_date"] - paid["due_date"]).dt.days
    overall = float(lateness.median()) if len(paid) else 0.0
    delay = pd.to_timedelta(book["customer_id"].map(lateness.groupby(paid["customer_id"]).median())
                            .fillna(overall).round(), unit="D")
    return {"naive_due": float(book.loc[book["due_date"] <= end, "amount"].sum()),
            "naive_median": float(book.loc[book["due_date"] + delay <= end, "amount"].sum()),
            "naive_rate": float(rate * book["amount"].sum())}


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
        end = t + pd.Timedelta(days=horizon)
        got = was_open & (full["true_paid_date"] <= end)
        actual = full.loc[got, "amount"].sum()
        lo, mid, hi = np.percentile(res["sim"].collections, [10, 50, 90])
        naive = naive_collections(obs, full[was_open], t, end)
        pct = lambda pred: (pred - actual) / actual * 100 if actual else float("nan")   # tahsilatsız dönem
        rows.append({"origin": t.date(), "actual": actual, "p10": lo, "p50": mid, "p90": hi,
                     "inside": lo <= actual <= hi, "err_p50_pct": pct(mid), **naive,
                     "err_due_pct": pct(naive["naive_due"]), "err_median_pct": pct(naive["naive_median"]),
                     "err_rate_pct": pct(naive["naive_rate"])})
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
