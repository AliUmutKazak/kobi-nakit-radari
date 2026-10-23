"""Uçtan uca kasa tahmini, giderler, döviz ve senaryolar."""

import numpy as np
import pandas as pd
import pytest

from radar import actions, pipeline
from radar.reconcile import reconcile
from radar.synthetic import generate, observe

from conftest import AS_OF


def test_pipeline_end_to_end(full):
    res = pipeline.demo(seed=3, as_of=AS_OF, n_sims=300)
    ranked = res["ranked"]
    assert len(ranked) == (res["obs"]["open_amount"] > 0).sum()
    assert ranked["actionable"].is_monotonic_decreasing and ranked["p_late"].between(0, 1).all()
    assert ranked.loc[ranked["actionable"], "amount_at_risk"].is_monotonic_decreasing
    drafts = [actions.draft_message(r, "Test A.Ş.") for _, r in ranked.iterrows()]
    assert all(d is None or d["requires_approval"] for d in drafts) and any(drafts)
    formal = [d for d in drafts if d and d["stage"] == "resmi"]
    assert all(d["note"] for d in formal)


def test_own_data_flow_matches_ground_truth(tmp_path):
    from radar import ingest
    from radar.synthetic import cash_plan, export_samples

    export_samples(tmp_path, seed=3, as_of=AS_OF)
    truth = observe(generate(seed=3, as_of=AS_OF), AS_OF)
    inv, notes = ingest.load_invoices(tmp_path / "faturalar.csv")
    assert len(inv) == len(truth) and inv["amount"].sum() == pytest.approx(truth["amount"].sum())
    assert inv["due_date"].notna().all() and not notes

    pay, _ = ingest.load_payments(tmp_path / "ekstre.csv")
    rec, alloc, unmatched = reconcile(inv, pay)
    # Türkçe başlık, 1.234,56 biçimi ve cari hesaba toplu ödemelerden sonra açık alacak aynı çıkmalı.
    assert rec["open_amount"].sum() == pytest.approx(truth["open_amount"].sum(), rel=1e-6)
    assert len(unmatched) == 0

    out = ingest.load_schedule(tmp_path / "giderler.csv")
    chq = ingest.load_schedule(tmp_path / "cekler.csv", "drawer")
    opening, _ = cash_plan(truth, AS_OF)
    base = pipeline.forecast(rec, AS_OF, opening, out, n_sims=300)
    with_chq = pipeline.forecast(rec, AS_OF, opening, out, n_sims=300, cheques=chq)
    gain = with_chq["sim"].p50[-1] - base["sim"].p50[-1]
    assert 0.8 * chq["amount"].sum() <= gain <= chq["amount"].sum() * 1.01


def test_backtest_on_own_data(full):
    obs = observe(full, AS_OF)
    bt = pipeline.backtest_own(obs, AS_OF, origins=2)
    assert len(bt) == 2 and (bt["p10"] <= bt["p90"]).all() and bt["actual"].gt(0).all()
    recent = obs[obs["issue_date"] > pd.Timestamp(AS_OF) - pd.Timedelta(days=200)]
    assert pipeline.backtest_own(recent, AS_OF) is None


def test_scenarios_and_gap_summary():
    res = pipeline.demo(seed=7, as_of=AS_OF, n_sims=400)
    sim = res["sim"]
    same = pipeline.scenario(res)
    assert np.allclose(same.p10, sim.p10) and np.allclose(same.p50, sim.p50)      # boş senaryo = bugünkü durum

    ids = list(res["ranked"].loc[res["ranked"]["actionable"], "invoice_id"])
    more = pipeline.scenario(res, ids[:10])
    assert np.all(more.p10[7:] >= sim.p10[7:] - 1e-6) and more.p10[-1] > sim.p10[-1]
    labels = ["Maaş"]
    late = pipeline.scenario(res, delay_labels=labels, delay_days=30)
    assert late.p50.min() >= sim.p50.min() - 1e-6 and late.p50[10] > sim.p50[10]

    gap = pipeline.gap_summary(res)
    assert sim.breach_day is not None and gap["gap"] > 0
    if gap["k"]:
        assert pipeline.scenario(res, ids[:gap["k"]]).breach_day is None
        assert gap["k"] == 1 or pipeline.scenario(res, ids[:gap["k"] - 1]).breach_day is not None


def test_payables_become_outflows_and_can_be_deferred(tmp_path):
    from radar import ingest
    from radar.synthetic import cash_plan, export_samples

    export_samples(tmp_path, seed=3, as_of=AS_OF)
    pay, notes = ingest.load_payables(tmp_path / "odenecekler.csv")
    obs = observe(generate(seed=3, as_of=AS_OF), AS_OF)
    _, plan = cash_plan(obs, AS_OF)
    supplier_total = plan.loc[plan["label"] == "Tedarikçi ödemeleri", "amount"].sum()
    assert pay["amount"].sum() == pytest.approx(supplier_total, rel=1e-6) and not notes
    assert (pay["label"] == ingest.PAYABLES_LABEL).all()

    p = tmp_path / "borc.csv"
    p.write_text("Tedarikçi;Fatura Tarihi;Vade;Tutar;Kalan\nA Ltd;01.08.2026;15.09.2026;1000;400\n"
                 "B AŞ;20.09.2026;;500;\n", encoding="utf-8")
    small, notes = ingest.load_payables(p)
    assert list(small["amount"]) == [400, 500] and small.at[1, "date"] == pd.Timestamp("2026-10-20")
    flows, late = ingest.payables_to_outflows(small, AS_OF)
    assert flows.at[0, "date"] == pd.Timestamp(AS_OF) + pd.Timedelta(days=1) and late

    out = ingest.load_schedule(tmp_path / "giderler.csv")
    flows, _ = ingest.payables_to_outflows(pay, AS_OF)
    res = pipeline.forecast(obs, AS_OF, 0.0, pd.concat([out, flows], ignore_index=True), n_sims=200)
    later = pipeline.scenario(res, delay_labels=[ingest.PAYABLES_LABEL], delay_days=30)
    assert later.p50[20] > res["sim"].p50[20]


def test_fixed_cost_plan_follows_tax_calendar():
    from radar.ingest import fixed_cost_plan

    plan = fixed_cost_plan("2026-10-14", 60, payroll=100, payroll_day=31, muhtasar=10, sgk=20, kdv=30)
    got = {(r.label, r.date.strftime("%d.%m")) for r in plan.itertuples()}
    assert ("Muhtasar", "26.10") in got and ("KDV", "28.10") in got
    assert ("SGK primi", "02.11") in got           # 31 Ekim 2026 Cumartesi -> Pazartesi
    assert ("KDV", "30.11") in got                  # 28 Kasım Cumartesi -> 30 Kasım Pazartesi
    assert ("Maaş", "31.10") in got and ("Maaş", "30.11") in got   # 31 olmayan ayda ay sonu


def test_weekly_plan_adds_up():
    res = pipeline.demo(seed=7, as_of=AS_OF, n_sims=300)
    week = pipeline.weekly_table(res)
    assert len(week) == 13 and week["Hafta"].iloc[0].startswith("02.10")
    out = res["outflows"]
    off = (out["date"] - pd.Timestamp(AS_OF)).dt.days
    assert week["Bilinen çıkışlar (TL)"].sum() == pytest.approx(out.loc[(off >= 1) & (off <= 91), "amount"].sum())
    assert (week["Hafta sonu kasa, kötümser (TL)"] <= week["Hafta sonu kasa, orta (P50) (TL)"]).all()
    assert week["Eksiye düşme olasılığı"].between(0, 1).all()


def test_invoice_impact_customer_delay_and_writeoff(tmp_path):
    from radar import pipeline
    from radar.store import Store

    res = pipeline.demo(seed=7, as_of=AS_OF, n_sims=400)
    ids = list(res["ranked"].loc[res["ranked"]["actionable"], "invoice_id"].head(5))
    impact = pipeline.invoice_impact(res, ids)
    assert len(impact) == 5 and (impact >= -1e-6).all()                  # gelmeyen para kasayı artıramaz
    same = pipeline.customer_delay(res, ["yok"], 30)
    assert np.allclose(same["p10"], res["sim"].p10)                       # kimse gecikmezse bant aynı
    big = res["obs"][res["obs"]["open_amount"] > 0].groupby("customer_id")["open_amount"].sum().idxmax()
    late = pipeline.customer_delay(res, [big], 60)
    assert late["amount"] > 0 and late["p10_min"] <= late["p10_min_before"] + 1e-6

    store = Store(tmp_path / "s.db")
    inv = res["obs"][["invoice_id", "customer_id", "customer_name", "amount", "open_amount", "paid_date",
                      "issue_date", "due_date"]]
    victim = inv.loc[inv["open_amount"] > 0, "invoice_id"].iloc[0]
    store.add_event(victim, "writeoff", "1", ts=AS_OF)
    out = store.apply_events(inv, AS_OF)
    row = out[out["invoice_id"] == victim].iloc[0]
    assert row["written_off"] and row["open_amount"] == 0 and pd.isna(row["paid_date"])
    store.add_event(victim, "writeoff", "0", ts=pd.Timestamp(AS_OF) + pd.Timedelta(hours=1))
    assert not store.apply_events(inv, AS_OF).set_index("invoice_id").at[victim, "written_off"]


def test_fx_exposure_and_scenario(tmp_path):
    from radar import ingest, pipeline

    path = tmp_path / "f.csv"
    rows = ["Fatura No;Cari Unvan;Fatura Tarihi;Vade Tarihi;Tutar;Para Birimi"]
    for k in range(60):
        day = pd.Timestamp("2025-10-01") + pd.Timedelta(days=6 * k)
        rows.append(f"F{k:04d};Müşteri {k % 6} A.Ş.;{day:%d.%m.%Y};{day + pd.Timedelta(days=30):%d.%m.%Y};"
                    f"{1000 + k};{'USD' if k % 3 == 0 else 'TL'}")
    path.write_text("\n".join(rows), encoding="utf-8")
    inv, _ = ingest.load_invoices(path, rates={"USD": 40.0})
    assert inv.loc[inv["currency"] == "USD", "fx_rate"].eq(40.0).all()
    res = pipeline.forecast(inv, "2026-10-01", 0.0, pd.DataFrame({"date": [], "amount": []}), n_sims=300)
    exp = pipeline.fx_exposure(res)
    usd_open = inv.loc[(inv["currency"] == "USD") & (inv["open_amount"] > 0), "open_amount"].sum()
    assert list(exp["currency"]) == ["USD"] and exp["receivable"].iloc[0] == pytest.approx(usd_open)
    up = pipeline.fx_shift(res, 0.2)
    assert up["p10_min"] >= up["p10_min_before"] - 1e-6 and (up["p50"] >= res["sim"].p50 - 1e-6).all()


def test_partial_payments_and_missing_due_scenarios():
    from radar.validation import run_case
    full = generate(seed=3, n_customers=30, partial_share=0.6)
    assert full["partial_frac"].between(0, 0.7).all() and (full["partial_frac"] > 0).any()
    # Kısmi ödemeler diğer senaryo çekilişlerini değiştirmez (eşleştirilmiş deneyler için).
    base = generate(seed=3, n_customers=30, cheque_share=0.4)
    pd.testing.assert_frame_equal(base, generate(seed=3, n_customers=30, cheque_share=0.4, partial_share=0.6)
                                  .drop(columns=["true_partial_date", "partial_frac"]))
    obs = observe(full, AS_OF)
    part = (obs["open_amount"] > 0) & (obs["open_amount"] < obs["amount"])
    assert part.any() and "partial_frac" not in obs
    r = run_case(5, 30, 0.6, 0.1, gen={"partial_share": 0.5, "missing_due": 0.3}, n_sims=200)[0]
    assert np.isfinite(r["err_p50_months"])


def test_unplanned_outflows_from_bank_history():
    as_of = pd.Timestamp("2026-10-01")
    bank = pd.DataFrame({"date": pd.date_range("2026-07-03", periods=90), "amount": 1000.0})   # ayda ~30.400 TL
    plan = pd.DataFrame({"date": [as_of + pd.Timedelta(days=d) for d in (5, 35, 65)], "amount": 10_000.0})  # ayda ~10.100
    rows, info = pipeline.unplanned_outflows(bank, plan, as_of)
    assert info["hist_month"] == pytest.approx(30_400, rel=0.01) and info["gap_month"] > 19_000
    assert rows["amount"].sum() == pytest.approx(info["gap_month"] * 90 / 30.4, rel=0.01)
    full_plan = pd.DataFrame({"date": [as_of + pd.Timedelta(days=d) for d in range(1, 91)], "amount": 1100.0})
    rows2, info2 = pipeline.unplanned_outflows(bank, full_plan, as_of)
    assert len(rows2) == 0 and info2["gap_month"] == 0
    assert pipeline.unplanned_outflows(bank.head(30), plan, as_of)[1] is None        # geçmiş kısa: karşılaştırma yok


def test_safe_to_spend_keeps_breach_probability_at_ten_percent():
    from radar.simulate import SimResult
    rng = np.random.default_rng(1)
    mins = rng.normal(100_000, 40_000, 5000)
    sim = SimResult(dates=None, p10=None, p50=None, p90=None, prob_negative=None, prob_any_breach=None,
                    min_balance=mins, breach_day=None, pay_day=None, collections=None, paths=None)
    s = pipeline.safe_to_spend(sim)
    assert ((mins - s) < 0).mean() == pytest.approx(0.10, abs=0.005)       # harcandığında eksiye düşme olasılığı %10
    sim2 = SimResult(dates=None, p10=None, p50=None, p90=None, prob_negative=None, prob_any_breach=None,
                     min_balance=mins - 300_000, breach_day=None, pay_day=None, collections=None, paths=None)
    assert pipeline.safe_to_spend(sim2) == 0.0


def test_outflow_levels_and_expected_shortfall():
    from radar.simulate import SimResult
    as_of = pd.Timestamp("2026-10-01")
    days = pd.date_range(as_of - pd.Timedelta(days=179), as_of)
    rng = np.random.default_rng(0)
    hist = pd.DataFrame({"date": days, "amount": np.repeat(rng.lognormal(0, 0.3, 6), 30) * 1000})
    lv = pipeline.outflow_levels(hist, as_of, 90, 500, seed=1)
    assert lv.shape == (3, 500) and np.allclose(lv.mean(axis=1), 1.0) and lv.std() > 0.1
    assert pipeline.outflow_levels(hist.tail(60), as_of, 90, 500, seed=1) is None        # 90 günden kısa geçmiş
    mins = np.linspace(-100, 900, 1000)
    sim = SimResult(dates=None, p10=None, p50=None, p90=None, prob_negative=None, prob_any_breach=None,
                    min_balance=mins, breach_day=None, pay_day=None, collections=None, paths=None)
    assert pipeline.expected_shortfall(sim) == pytest.approx(mins[:100].mean())


def test_cash_components_and_component_variance():
    import json
    from radar import pilot
    res = pipeline.demo(seed=3, as_of=AS_OF, n_sims=200)
    comp = pilot.cash_components(res)
    assert set(comp) == {"7", "14", "28"} and comp["28"]["acik"] >= comp["7"]["acik"] >= 0
    rec = pd.DataFrame([{"as_of": "2026-09-01", "target": "kasa", "horizon": 28, "until": "2026-09-25",
                         "meta": json.dumps({"bilesenler": {"28": {"acik": 1000, "yeni": 500, "gider": 800}}})}])
    obs = pd.DataFrame({"invoice_id": ["A", "B"], "issue_date": pd.to_datetime(["2026-08-01", "2026-09-10"]),
                        "paid_date": pd.to_datetime(["2026-09-05", "2026-09-25"])})
    ev = pd.DataFrame({"date": pd.to_datetime(["2026-09-05", "2026-09-25"]), "invoice_id": ["A", "B"], "amount": [900.0, 300.0]})
    bank = pd.DataFrame({"date": pd.to_datetime(["2026-09-10"]), "amount": [1000.0]})
    v = pilot.component_variance(rec, obs, ev, bank).set_index("kalem")
    assert v.loc["Açık faturalardan tahsilat", "fark"] == -100 and v.loc["Yeni satışlardan tahsilat", "gerceklesen"] == 300
    assert v.loc["Giderler", "fark"] == 200


def test_tax_payments_move_past_official_holidays():
    from radar import ingest
    # Nisan 2026 KDV'sinin son günü 28 Mayıs: Kurban Bayramı (27-30 Mayıs) ve hafta sonu, ilk iş günü 1 Haziran.
    assert ingest.next_business_day("2026-05-28") == pd.Timestamp("2026-06-01")
    assert ingest.next_business_day("2026-05-26") == pd.Timestamp("2026-05-26")        # arife yarım gün: iş günü
    assert ingest.next_business_day("2026-10-29") == pd.Timestamp("2026-10-30")        # Cumhuriyet Bayramı
    plan = ingest.fixed_cost_plan("2026-05-01", horizon=40, kdv=1000.0)
    assert list(plan["date"]) == [pd.Timestamp("2026-06-01")]


def test_fx_uncertainty_widens_pessimistic_band(full):
    obs = observe(full, AS_OF).copy()
    usd = obs["customer_id"].isin(obs["customer_id"].unique()[:10])
    obs["currency"] = np.where(usd, "USD", "TRY")
    obs["fx_rate"] = np.where(usd, 49.5, 1.0)
    out = pd.DataFrame({"date": [], "amount": []})
    on = pipeline.forecast(obs, AS_OF, 0.0, out, n_sims=400)
    off = pipeline.forecast(obs, AS_OF, 0.0, out, n_sims=400, fx_aware=False)
    assert on["info"]["fx_currencies"] == ["USD"] and on["info"]["fx_unknown"] == []
    assert on["sim"].p10[-1] < off["sim"].p10[-1]                       # kur düşüşü kötümser uca girdi
    assert on["sim"].p50[-1] == pytest.approx(off["sim"].p50[-1], rel=0.03)
    # Senaryo hesapları aynı kur yollarını kullanır (satırlar hizalı kalır).
    assert pipeline.scenario(on).p50[-1] == pytest.approx(on["sim"].p50[-1])


def test_foreign_currency_payables_are_converted_and_add_fx_risk(tmp_path, full):
    from radar import ingest
    path = tmp_path / "borc.csv"
    path.write_text("Fatura No;Tedarikçi;Vade Tarihi;Tutar;Para Birimi\n"
                    "B1;Ithalatci;15.11.2026;10.000,00;USD\nB2;Yerel;20.11.2026;50.000,00;TL\n"
                    "B3;Isvicre;25.11.2026;1.000,00;CHF\n", encoding="utf-8")
    pay, notes = ingest.load_payables(path, rates={"USD": 49.5})
    assert pay["amount"].tolist() == [495000.0, 50000.0, 1000.0] and pay["currency"].tolist() == ["USD", "TRY", "TRY"]
    assert any("DİKKAT" in n and "CHF" in n for n in notes)          # kuru girilmeyen borç dışarıda bırakılmaz
    flows, _ = ingest.payables_to_outflows(pay, AS_OF)
    obs = observe(full, AS_OF)
    on = pipeline.forecast(obs, AS_OF, 1e6, flows, n_sims=400)
    off = pipeline.forecast(obs, AS_OF, 1e6, flows, n_sims=400, fx_aware=False)
    assert on["info"]["fx_currencies"] == ["USD"] and on["info"]["fx_short"] == ["USD"]
    assert on["sim"].p10[-1] < off["sim"].p10[-1]                    # kur yükselirse borç büyür
    assert on["sim"].p50[-1] < off["sim"].p50[-1]                    # borç ağırlıklıda TL'nin değer kaybı sürer
    exp = pipeline.fx_exposure(on)
    assert exp.loc[0, "payable"] == pytest.approx(495000.0) and exp.loc[0, "net"] < 0
    up = pipeline.fx_shift(on, 0.10)                                  # TL %10 değer kaybederse borç 49.500 TL büyür
    assert up["p50"][-1] == pytest.approx(on["sim"].p50[-1] - 49500.0, abs=1.0)


def test_foreign_currency_schedule_and_cheques(tmp_path, full):
    from radar import ingest
    (tmp_path / "gider.csv").write_text("Tarih;Tutar;Kalem;Para Birimi\n05.11.2026;1.000,00;Lisans;USD\n"
                                        "10.11.2026;500,00;Yazılım;GBP\n12.11.2026;20.000,00;Maaş;TL\n", encoding="utf-8")
    notes = []
    out = ingest.load_schedule(tmp_path / "gider.csv", rates={"USD": 49.5}, notes=notes)
    assert out["amount"].tolist() == [49500.0, 500.0, 20000.0] and out["currency"].tolist() == ["USD", "TRY", "TRY"]
    assert any(n.startswith("DİKKAT") and "GBP" in n for n in notes)  # gider dışarıda bırakılmaz, uyarılır
    (tmp_path / "cek.csv").write_text("Vade;Tutar;Keşideci;Para Birimi\n20.11.2026;2.000,00;Ihracatci;EUR\n"
                                      "25.11.2026;300,00;Isvicre;CHF\n", encoding="utf-8")
    chq, cn = ingest.load_cheques(tmp_path / "cek.csv", rates={"EUR": 55.6})
    assert chq["amount"].tolist() == [111200.0] and chq["currency"].tolist() == ["EUR"]   # kuru olmayan giriş katılmaz
    assert any("CHF" in n and "katılmadı" in n for n in cn)
    obs = observe(full, AS_OF)
    on = pipeline.forecast(obs, AS_OF, 1e6, out, n_sims=400, cheques=chq)
    assert sorted(on["info"]["fx_currencies"]) == ["EUR", "USD"] and on["info"]["fx_short"] == ["USD"]
    exp = pipeline.fx_exposure(on).set_index("currency")
    assert exp.loc["EUR", "receivable"] == pytest.approx(111200.0) and exp.loc["USD", "payable"] == pytest.approx(49500.0)


def test_cheques_marked_risky_are_not_counted(tmp_path):
    from radar import ingest
    (tmp_path / "cek.csv").write_text("Vade;Tutar;Keşideci;Durum\n20.11.2026;10.000,00;A;portföyde\n"
                                      "21.11.2026;5.000,00;B;Riskli\n22.11.2026;3.000,00;C;ciro edildi\n"
                                      "23.11.2026;2.000,00;D;Şüpheli\n", encoding="utf-8")
    chq, notes = ingest.load_cheques(tmp_path / "cek.csv")
    assert chq["amount"].tolist() == [10000.0]
    assert any(n.startswith("DİKKAT") and "2 çek" in n for n in notes)


def test_findeks_probability_replaces_country_average_for_that_cheque(full):
    from radar import ingest
    import io
    csv = ("Vade;Tutar;Keşideci;Findeks ödeme olasılığı\n20.10.2026;100.000,00;A;%60\n"
           "25.10.2026;100.000,00;B;\n27.10.2026;50.000,00;C;140\n")
    chq, notes = ingest.load_cheques(io.BytesIO(csv.encode("utf-8")))
    assert chq["pay_prob"].iloc[0] == pytest.approx(0.60) and chq["pay_prob"].iloc[1:].isna().all()
    assert any("Findeks" in n and "1 çekte, karşılıksız" in n for n in notes) and any("okunamadı" in n for n in notes)
    obs = observe(full, AS_OF)
    out = pd.DataFrame({"date": [], "amount": []})
    base = pipeline.forecast(obs, AS_OF, 0.0, out, n_sims=400, cheques=chq.drop(columns="pay_prob"))
    risky = pipeline.forecast(obs, AS_OF, 0.0, out, n_sims=400, cheques=chq)
    # Ülke ortalaması (%3,4 karşılıksızlık) yerine %40: A çekinin beklenen katkısı yaklaşık 36.600 TL azalır.
    drop = base["sim"].paths[:, -1].mean() - risky["sim"].paths[:, -1].mean()
    assert 25_000 < drop < 50_000
