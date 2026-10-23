"""Gecikme modeli, kalibrasyon ve Monte Carlo simülasyonu."""

import numpy as np
import pandas as pd
import pytest

from radar import pipeline, simulate as sim_mod
from radar.synthetic import generate, observe

from conftest import AS_OF


def test_quantile_function_is_consistent():
    q = np.array([-2.0, 0.0, 5.0, 14.0, 30.0])
    u = np.linspace(0.001, 0.999, 500)
    x = sim_mod.ppf(q, u)
    assert np.all(np.diff(x) >= 0)
    assert np.allclose([sim_mod.cdf(q, v) for v in x], u, atol=1e-6)


def test_simulation_respects_time_and_ordering():
    as_of = pd.Timestamp(AS_OF)
    inv = pd.DataFrame({
        "customer_id": ["A", "A", "B"],
        "issue_date": as_of - pd.to_timedelta([100, 40, 10], unit="D"),
        "due_date": as_of - pd.to_timedelta([70, 10, -20], unit="D"),
        "open_amount": [100.0, 200.0, 300.0], "p_default": [0.02, 0.02, 0.02], "projected": False,
    })
    Q = np.tile([-2.0, 0.0, 5.0, 14.0, 30.0], (3, 1))
    out = pd.DataFrame({"date": [as_of + pd.Timedelta(days=5)], "amount": [150.0]})
    res = sim_mod.simulate(inv, Q, as_of, 50.0, out, horizon=60, n_sims=500)
    assert res.pay_day.min() >= 1                     # 70 gün gecikmiş fatura geçmişte ödenemez
    assert np.all(res.p10 <= res.p50) and np.all(res.p50 <= res.p90)
    assert res.p50[0] == 50.0 and res.collections.max() <= 600.0


def test_model_is_scored_against_baseline(full):
    bt = pipeline.backtest_model(full, AS_OF)
    assert bt["n"] > 50 and 0.5 <= bt["coverage_p10_p90"] <= 0.98
    assert bt["mae_model"] < bt["mae_baseline"] * 1.15


def test_small_dataset_uses_simple_model(full):
    small = observe(full, AS_OF).tail(60).reset_index(drop=True)
    res = pipeline.forecast(small, AS_OF, 0.0, pd.DataFrame({"date": [], "amount": []}), n_sims=200)
    assert res["simple_model"] and np.all(res["sim"].p10 <= res["sim"].p90)


def test_correlation_is_estimated_from_data():
    from radar.simulate import PRIOR_RHO, estimate_correlation

    rng = np.random.default_rng(0)
    n, n_cust = 3000, 30
    cust = rng.integers(0, n_cust, n)
    due = pd.Timestamp("2024-01-01") + pd.to_timedelta(rng.integers(0, 720, n), unit="D")
    quarter = pd.PeriodIndex(due, freq="Q").astype(str)
    Q = np.tile([-12.8, -6.7, 0.0, 6.7, 12.8], (n, 1))             # N(0, 10) dağılımının kantilleri

    def rho(market_sd, cust_sd):
        m = pd.Series(rng.normal(0, market_sd, quarter.nunique()), index=quarter.unique())
        keys = pd.Series(cust.astype(str)) + quarter
        c = pd.Series(rng.normal(0, cust_sd, keys.nunique()), index=keys.unique())
        idio = np.sqrt(max(1 - market_sd ** 2 - cust_sd ** 2, 0))
        y = 10 * (m[quarter].to_numpy() + c[keys].to_numpy() + idio * rng.standard_normal(n))
        return estimate_correlation(Q, y, cust, due)

    none = rho(0.0, 0.0)
    strong = rho(0.0, np.sqrt(0.4))
    assert none[1] < 0.05 and 0.25 < strong[1] < 0.55               # müşteri etkisi veriden bulunuyor
    assert estimate_correlation(Q[:50], np.zeros(50), cust[:50], due[:50]) == PRIOR_RHO


def test_censored_fit_recovers_mean_that_naive_average_misses():
    from radar.simulate import censored_normal_fit

    rng = np.random.default_rng(1)
    true = rng.normal(0.4, 1.2, 4000)
    limit = rng.normal(1.0, 0.5, 4000)                    # gözlem penceresi: bundan büyük değerler görülemez
    censored = true > limit
    seen = np.where(censored, limit, true)
    mu, sigma = censored_normal_fit(seen, censored)
    assert seen.mean() < 0.25 and abs(mu - 0.4) < 0.08 and abs(sigma - 1.2) < 0.08
    assert censored_normal_fit(true, np.zeros(4000, bool)) == pytest.approx((true.mean(), true.std()))


def test_calibration_detects_worsening_payment_behaviour():
    steady = pipeline.calibrate(observe(generate(seed=5, trend=0.0, as_of=AS_OF), AS_OF), AS_OF)
    worse = pipeline.calibrate(observe(generate(seed=5, trend=1.5, as_of=AS_OF), AS_OF), AS_OF)
    assert steady["fresh"]["n"] > 100 and 0 <= steady["rho_market"] <= 0.5
    # Ödemeler kötüleşirken gerçekleşenler tahmin dağılımının geç tarafına düşer: yeniden ayar eğrisinin
    # ortası (tekdüze sayı 0,5'in karşılığı) kötüleşen şirkette daha yukarıda olmalı.
    assert worse["fresh"]["recal"][50] > steady["fresh"]["recal"][50]


def test_combined_model_recalibration_and_widening():
    from radar.model import CombinedModel, fit_model
    from radar.simulate import RECAL_GRID, pit_recalibration

    full = generate(seed=2, n_customers=20, as_of=AS_OF)
    obs = observe(full, AS_OF)
    from radar.model import training_frame
    X, y = training_frame(obs, AS_OF)
    m = fit_model(X, y)
    assert isinstance(m, CombinedModel)
    Q = m.predict(X.head(50))
    assert (np.diff(Q, axis=1) >= -1e-9).all()                            # kantiller sıralı kalır
    rng = np.random.default_rng(0)
    from scipy.special import ndtri
    calibrated = pit_recalibration(ndtri(rng.uniform(0.001, 0.999, 2000)), np.zeros(2000, bool), 30.0)
    assert np.abs(calibrated - RECAL_GRID).max() < 0.05                    # PIT tekdüzeyse dokunulmaz
    early = pit_recalibration(ndtri(rng.uniform(0.001, 0.999, 2000) ** 2), np.zeros(2000, bool), 30.0)
    assert early[50] < 0.35 and (np.diff(early) >= 0).all()               # erken gerçekleşme: kantil aşağı kayar
    res = pipeline.demo(seed=2, as_of=AS_OF, n_sims=300)
    assert res["info"]["widen"] >= 1.0 and res["ctx"]["calib"]["fresh"].get("recal") is not None


def test_sales_method_is_chosen_by_own_history_and_level_is_unbiased():
    rng = np.random.default_rng(4)
    days = pd.date_range("2024-01-01", "2026-09-30", freq="D")

    def book(seasonal: bool) -> pd.DataFrame:
        base = 1000 * (1 + (0.9 * np.sin(2 * np.pi * days.dayofyear / 365) if seasonal else 0))
        amount = np.maximum(base * rng.lognormal(0, 0.15, len(days)), 1)
        return pd.DataFrame({"invoice_id": [f"F{i}" for i in range(len(days))], "customer_id": "1",
                             "issue_date": days, "due_date": days + pd.Timedelta(days=30), "amount": amount})
    as_of = pd.Timestamp("2026-09-30")
    assert pipeline.sales_method(book(True), as_of, 90) == "mevsimsel"     # güçlü mevsimsellik: geçen yıl
    assert pipeline.sales_method(book(False), as_of, 90) == "hiz"          # mevsimsellik yok: anlamlı fark yok
    short = book(True)[lambda d: d["issue_date"] > "2026-01-01"]
    assert pipeline.sales_method(short, as_of, 90) == "hiz"                # bir yıldan kısa geçmiş
    res = pipeline.demo(seed=7, as_of=AS_OF, n_sims=400)
    lvl = res["ctx"]["sales_level"]
    assert lvl is not None and np.allclose(lvl.mean(axis=1), 1.0) and res["info"]["sales_errors_n"] >= 8


def test_cheque_payers_cash_arrives_at_cheque_maturity():
    from radar.validation import run_case
    # Müşterilerin yarısı 90 gün vadeli çekle öder: düzeltme yoksa kasa olduğundan dolu görünür.
    off = run_case(5, 40, 0.6, 0.1, gen={"cheque_share": 0.5, "cheque_term": 90},
                   forecast_kwargs={"cheque_aware": False}, n_sims=300)[0]
    on = run_case(5, 40, 0.6, 0.1, gen={"cheque_share": 0.5, "cheque_term": 90}, n_sims=300)[0]
    assert off["err_p50_months"] > 0.8 and abs(on["err_p50_months"]) < 0.4
    full = generate(seed=5, n_customers=20, cheque_share=0.5)
    habits = pipeline.cheque_habits(observe(full, AS_OF), AS_OF)
    assert 0.1 < habits["overall"] < 0.95 and 50 < habits["median_term"] < 110
    assert pipeline.cheque_habits(observe(generate(seed=5, n_customers=20), AS_OF), AS_OF) is None


def test_sales_growth_is_shrunk_and_follows_inflation():
    flat = [pipeline.sales_growth(observe(generate(seed=s, n_customers=40), AS_OF), AS_OF) for s in range(3)]
    hot = [pipeline.sales_growth(observe(generate(seed=s, n_customers=40, inflation=0.5), AS_OF), AS_OF) for s in range(3)]
    assert all(abs(g - 1) < 0.2 for g in flat) and all(1.2 < g < 1.9 for g in hot) and min(hot) > max(flat)
    short = observe(generate(seed=1, n_customers=20, months=12), AS_OF)
    assert pipeline.sales_growth(short, AS_OF) == 1.0                 # bir buçuk yıldan kısa geçmiş: büyüme yok


def test_installment_habits_are_learned_from_collection_events():
    from radar.synthetic import payment_events
    full = generate(seed=3, n_customers=40, partial_share=0.5)
    obs, ev = observe(full, AS_OF), payment_events(full[full["issue_date"] <= AS_OF], AS_OF)
    h = pipeline.installment_habits(obs, ev, AS_OF)
    truth = ((full["partial_frac"] > 0) & full["true_paid_date"].notna()).mean()
    assert abs(h["overall"] - truth) < 0.1 and 0.3 < h["median_frac"] < 0.7
    plain = generate(seed=3, n_customers=40)
    assert pipeline.installment_habits(observe(plain, AS_OF), payment_events(plain, AS_OF), AS_OF) is None
    assert pipeline.installment_habits(obs, None, AS_OF) is None
    # Taksit bilgisi verilince ilk taksitler kapanıştan önce gelir: orta tahmin yükselir.
    from radar.synthetic import cash_plan
    _, out = cash_plan(obs, AS_OF)
    off = pipeline.forecast(obs, AS_OF, 0.0, out, n_sims=300)
    on = pipeline.forecast(obs, AS_OF, 0.0, out, n_sims=300, events=ev)
    assert on["sim"].p50[30] > off["sim"].p50[30] and on["info"]["installment_n"] > 0


def test_fx_paths_use_only_past_data_and_no_drift():
    from radar import fx
    paths = fx.fx_paths(["USD", "EUR", "XYZ"], "2026-10-01", 90, 2000, seed=1)
    assert set(paths) == {"USD", "EUR"}                                 # ECB tablosunda olmayan döviz eklenmez
    assert paths["USD"].shape == (2000, 91) and np.allclose(paths["USD"][:, 0], 1.0)
    # Sürüklenme çıkarıldı: TL'nin geçmişteki değer kaybı geleceğe taşınmaz (log ortalaması ~0).
    assert abs(np.log(paths["USD"][:, -1]).mean()) < 0.02
    assert np.quantile(paths["USD"][:, -1], 0.10) < 0.97                 # kötümser uçta kur düşüşü var
    assert fx.fx_paths(["USD"], "2006-01-01", 90, 100, seed=1) == {}     # iki yıldan kısa geçmiş
    short = fx.fx_paths(["USD"], "2026-10-01", 90, 2000, seed=1, short=["USD"])["USD"]
    assert np.median(short[:, -1]) > 1.0                                  # borç ağırlıklı: son 3 yılın değer kaybı


def test_fx_conformal_widening_only_widens():
    from radar import fx
    for short in (False, True):
        for side in ("lo", "up"):
            k = fx.conformal_k("USD", "2026-10-01", 60, side, short)
            assert 1.0 <= k <= 3.0
    # Borç tarafında son yıllarda kur sıçramaları %10'dan sık aştığı için bant açıldı.
    assert fx.conformal_k("USD", "2026-10-01", 60, "up", False) > 1.0
