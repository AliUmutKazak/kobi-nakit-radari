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

from .pipeline import forecast, payments_cutoff
from .synthetic import cash_plan, cheque_portfolio, generate, observe, payment_events

REGIMES = {
    "customers": [8, 40],        # müşteri sayısı: yoğunlaşma riski
    "trend": [0.0, 1.2],         # gecikmelerin dönem içinde kötüleşme hızı
    "shock": [0.0, 0.3],         # çeyreklik ortak piyasa şoku (tahmin dönemindeki şok bilinmez)
}
OPENINGS = [0.2, 0.45, 0.8]      # açılış kasası (aylık ciro cinsinden); aynı tahminden türetilir


def run_case(seed: int, customers: int, trend: float, shock: float, as_of="2026-07-01",
             horizon: int = 90, n_sims: int = 1000, calib_hook=None, gen: dict | None = None,
             forecast_kwargs: dict | None = None) -> list[dict]:
    """gen: senaryo laboratuvarının ek üretici ayarları (synthetic.generate; bkz. lab.py).
    forecast_kwargs: pipeline.forecast'a ek ayarlar (deneylerde bir düzeltmeyi kapatıp açmak için).
    Tahsilat kayıt gecikmesi (gen["record_lag"]) varsa kesim günü forecast_kwargs["cutoff"] ile seçilir:
    "auto" (varsayılan; ürünün kendi tahmini, pipeline.payments_cutoff), "true" (kullanıcı gerçek tarihi girer),
    "none" (düzeltme yok)."""
    as_of = pd.Timestamp(as_of)
    end = as_of + pd.Timedelta(days=horizon)
    gen = dict(gen or {})
    record_lag = int(gen.pop("record_lag", 0))
    missing_due = float(gen.pop("missing_due", 0.0))
    outflow_sigma = float(gen.pop("outflow_sigma", 0.0))
    full = generate(seed=seed, n_customers=customers, as_of=end, trend=trend, shock=shock, **gen)
    obs = observe(full, as_of, record_lag)
    if missing_due:
        # Veri kalitesi: vadesi girilmemiş faturalar; panel bunlara varsayılan vadeyi (30 gün, TTK m.1530/4-a) verir.
        miss = np.random.default_rng(seed + 20_000).random(len(obs)) < missing_due
        obs.loc[miss, "due_date"] = obs.loc[miss, "issue_date"] + pd.Timedelta(days=30)
    _, outflows = cash_plan(obs, as_of, horizon)
    realized, history = outflows, None
    kw = dict(forecast_kwargs or {})
    outflow_aware = kw.pop("outflow_aware", True)
    if outflow_sigma:
        # Giderler 30 günlük bloklarda dalgalanır (log-normal, ortalaması plana eşit). Banka geçmişi aynı süreçten:
        # tahmin planı ve geçmişi görür, gerçekleşen kasa dalgalanan giderlerle hesaplanır.
        rng = np.random.default_rng(seed + 50_000)
        def noisy(plan, start):
            block = ((plan["date"] - start).dt.days.clip(lower=1) - 1) // 30
            f = rng.lognormal(-outflow_sigma ** 2 / 2, outflow_sigma, int(block.max()) + 1)
            return plan.assign(amount=plan["amount"] * f[block.to_numpy()])
        past_start = as_of - pd.Timedelta(days=180)
        history = noisy(cash_plan(obs, past_start, 180)[1], past_start)[["date", "amount"]]
        realized = noisy(outflows, as_of)
    if outflow_aware and history is not None:
        kw["outflow_history"] = history
    mode = kw.pop("cutoff", "auto")
    through = {"auto": payments_cutoff(obs, as_of), "true": as_of - pd.Timedelta(days=record_lag), "none": None}[mode]
    res = forecast(obs, as_of, 0.0, outflows, horizon, n_sims, seed=seed, calib_hook=calib_hook,
                   cheques=cheque_portfolio(obs, as_of), payments_through=through,
                   events=payment_events(full[full["issue_date"] <= as_of], as_of, record_lag), **kw)
    sim = res["sim"]

    # Gerçekleşen yol: tahmin tarihinden sonra kesilenler dahil tüm faturaların paranın gerçekten geldiği günler
    # (çekle ödenende çek vadesi; karşılıksız çek hiç gelmez).
    cash = full["true_cash_date"] if "true_cash_date" in full else full["true_paid_date"]
    rest = full["amount"] * (1 - full["partial_frac"]) if "partial_frac" in full else full["amount"]
    paid = full[(cash > as_of) & (cash <= end)]
    flow = np.zeros(horizon + 1)
    np.add.at(flow, (cash[paid.index] - as_of).dt.days.to_numpy(), rest[paid.index].to_numpy())
    if "true_partial_date" in full:                              # ilk taksitler
        first = full[(full["true_partial_date"] > as_of) & (full["true_partial_date"] <= end)]
        np.add.at(flow, (first["true_partial_date"] - as_of).dt.days.to_numpy(),
                  (first["amount"] * first["partial_frac"]).to_numpy())
    np.add.at(flow, (realized["date"] - as_of).dt.days.to_numpy(), -realized["amount"].to_numpy())
    truth = np.cumsum(flow)

    monthly = obs.loc[obs["issue_date"] > as_of - pd.Timedelta(days=180), "amount"].sum() / 6
    baselines = baseline_paths(obs, res["ctx"]["sim_inv"], outflows, as_of, horizon)
    alpha = 0.2                                             # %80 aralık için aralık skoru (Gneiting ve Raftery 2007)
    lo, hi, y = sim.p10[-1], sim.p90[-1], truth[-1]
    interval_score = (hi - lo) + 2 / alpha * max(lo - y, 0) + 2 / alpha * max(y - hi, 0)
    errors = {"err_final_model": abs(sim.p50[-1] - truth[-1]) / monthly,
              "err_min_model": abs(sim.p50[1:].min() - truth[1:].min()) / monthly,
              "interval_score": interval_score / monthly}
    for name, path in baselines.items():
        errors[f"err_final_{name}"] = abs(path[-1] - truth[-1]) / monthly
        errors[f"err_min_{name}"] = abs(path[1:].min() - truth[1:].min()) / monthly
    base = errors | {"seed": seed, "customers": customers, "trend": trend, "shock": shock, "n_invoices": len(obs),
            "simple_model": res["simple_model"], "rho_market": res["ctx"]["calib"]["rho_market"], "rho_customer": res["ctx"]["calib"]["rho_customer"],
            "z_shift": res["ctx"]["calib"]["fresh"]["z_shift"], "z_shift_overdue": res["ctx"]["calib"]["overdue"]["z_shift"],
            "z_scale": res["ctx"]["calib"]["fresh"]["z_scale"], "z_scale_overdue": res["ctx"]["calib"]["overdue"]["z_scale"],
            "err_p50_months": (sim.p50[-1] - truth[-1]) / monthly,
            "inside": bool(sim.p10[-1] <= truth[-1] <= sim.p90[-1]),
            "below": bool(truth[-1] < sim.p10[-1]), "above": bool(truth[-1] > sim.p90[-1])}
    # Açılış kasası yalnızca tüm yolları sabit kadar kaydırır; aynı senaryolardan üç ayrı şirket durumu çıkar.
    return [base | {"opening_months": m, "p_breach": float((sim.min_balance + m * monthly < 0).mean()),
                    "breached": bool(truth[1:].min() + m * monthly < 0)}
            | {f"breach_{name}": float(path[1:].min() + m * monthly < 0) for name, path in baselines.items()}
            for m in OPENINGS]


BASELINES = {"vade": "Sözleşme vadesinde ödenir", "medyan": "Müşteri her zamanki kadar geç öder",
             "hiz": "Son 90 günün günlük tahsilat hızı sürer"}


def baseline_paths(obs: pd.DataFrame, target: pd.DataFrame, outflows: pd.DataFrame, as_of, horizon: int) -> dict:
    """Basit, deterministik kasa tahminleri (açılış 0). Model bunları yenmeden "akıllı" sayılmaz.

    target: modelin simüle ettiği faturalar (açık + gelecek satış tahmini); adil olsun diye aynı küme."""
    as_of = pd.Timestamp(as_of)
    out = np.zeros(horizon + 1)
    off = (outflows["date"] - as_of).dt.days.to_numpy()
    keep = (off >= 1) & (off <= horizon)
    np.add.at(out, off[keep], outflows["amount"].to_numpy()[keep])

    paid = obs.dropna(subset=["paid_date"])
    delay = (paid["paid_date"] - paid["due_date"]).dt.days
    med = delay.groupby(paid["customer_id"]).median()
    overall = float(delay.median()) if len(delay) else 0.0
    earliest = np.maximum((target["issue_date"] - as_of).dt.days.to_numpy(), 0) + 1
    due = (target["due_date"] - as_of).dt.days.to_numpy()
    amount = target["open_amount"].to_numpy(float)

    def path(days):
        flow = np.zeros(horizon + 1)
        days = np.maximum(days, earliest)
        ok = days <= horizon
        np.add.at(flow, days[ok].astype(int), amount[ok])
        return np.cumsum(flow - out)

    recent = paid[(paid["paid_date"] > as_of - pd.Timedelta(days=90)) & (paid["paid_date"] <= as_of)]
    daily = recent["amount"].sum() / 90
    rate = np.cumsum(np.r_[0.0, np.full(horizon, daily)] - out)
    return {"vade": path(due),
            "medyan": path(due + np.round(target["customer_id"].map(med).fillna(overall).to_numpy())),
            "hiz": rate}


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

    def paired(model_col, base_col, frame):
        d = frame[model_col] - frame[base_col]
        return f"{d.mean():+.3f} ±{d.std() / np.sqrt(len(d)):.3f}"

    rows = [{"yöntem": "Model (P50 / olasılık)", "dönem_sonu_hata": cases["err_final_model"].mean(),
             "en_düşük_kasa_hatası": cases["err_min_model"].mean(),
             "brier": float(np.mean((df["p_breach"] - df["breached"]) ** 2)),
             "fark_dönem_sonu": "", "fark_en_düşük": "", "fark_brier": ""}]
    df = df.assign(se_model=(df["p_breach"] - df["breached"]) ** 2)
    for name, label in BASELINES.items():
        df[f"se_{name}"] = (df[f"breach_{name}"] - df["breached"]) ** 2
        rows.append({"yöntem": label, "dönem_sonu_hata": cases[f"err_final_{name}"].mean(),
                     "en_düşük_kasa_hatası": cases[f"err_min_{name}"].mean(), "brier": df[f"se_{name}"].mean(),
                     "fark_dönem_sonu": paired("err_final_model", f"err_final_{name}", cases),
                     "fark_en_düşük": paired("err_min_model", f"err_min_{name}", cases),
                     "fark_brier": paired("se_model", f"se_{name}", df)})
    baseline_table = pd.DataFrame(rows).set_index("yöntem")
    return {
        "baselines": baseline_table, "interval_score": float(cases["interval_score"].mean()),
        "n_cases": len(cases), "n_rows": len(df),
        "coverage": _rate(cases["inside"]), "below_p10": _rate(cases["below"]), "above_p90": _rate(cases["above"]),
        "bias_months": f"{err.mean():+.2f} ±{err.std() / np.sqrt(len(err)):.2f}",
        "brier": float(np.mean((df["p_breach"] - df["breached"]) ** 2)),
        "brier_baseline": float(base * (1 - base)),
        "reliability": reliability,
        "by_regime": {k: table(k) for k in REGIMES},
        "standards": standards_summary(cases, df),
    }


def standards_summary(cases: pd.DataFrame, df: pd.DataFrame) -> dict:
    """Uluslararası testler: dönem sonu kasa bandı için Basel bölgesi (alt uç) ve Kupiec (alt, üst, merkezi);
    eksiye düşme olasılıkları için Spiegelhalter ve Brier. Her açılış düzeyi ayrı satır olduğu için
    Spiegelhalter gözlemleri tam bağımsız değildir; sonuç bu nedenle temkinli okunur."""
    from .standards import basel_zone, corp, kupiec_pof, spiegelhalter
    n, below, above = len(cases), int(cases["below"].sum()), int(cases["above"].sum())
    return {"basel_lower": basel_zone(n, below, 0.10), "kupiec_lower": kupiec_pof(n, below, 0.10),
            "kupiec_upper": kupiec_pof(n, above, 0.10), "kupiec_central": kupiec_pof(n, below + above, 0.20),
            "spiegelhalter": spiegelhalter(df["p_breach"], df["breached"]),
            "corp": corp(df["p_breach"], df["breached"])}
