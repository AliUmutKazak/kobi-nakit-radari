from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from radar import actions, pipeline, simulate as sim_mod
from radar.reconcile import reconcile
from radar.synthetic import generate, observe, to_ubl_xml
from radar.ubl import parse_invoice

AS_OF = "2026-10-01"


@pytest.fixture(scope="module")
def full():
    return generate(seed=3, n_customers=25, months=18, as_of=AS_OF)


def test_ubl_roundtrip_and_missing_due_date(full):
    row = full.iloc[0]
    parsed = parse_invoice(to_ubl_xml(row))
    assert parsed["invoice_id"] == row["invoice_id"] and parsed["vkn"] == row["vkn"]
    assert parsed["due_date"] == row["due_date"].normalize() and parsed["due_source"] == "payment_means"
    assert parsed["amount"] == pytest.approx(row["amount"])

    no_due = parse_invoice(to_ubl_xml(row, with_due_date=False))
    assert no_due["due_date"] is None and no_due["due_source"] == "missing"
    fallback = parse_invoice(to_ubl_xml(row, with_due_date=False), default_terms_days=45)
    assert fallback["due_date"] == row["issue_date"].normalize() + pd.Timedelta(days=45)


def test_reconcile_exact_then_fifo_partial():
    inv = pd.DataFrame({
        "invoice_id": ["A1", "A2", "B1"], "customer_id": ["A", "A", "B"],
        "customer_name": ["Toros Makine Sanayi A.Ş.", "Toros Makine Sanayi A.Ş.", "Ege Gıda Pazarlama A.Ş."],
        "vkn": ["1111111111", "1111111111", "2222222222"],
        "due_date": pd.to_datetime(["2026-08-01", "2026-09-01", "2026-09-10"]),
        "open_amount": [1000.0, 500.0, 800.0],
    })
    pay = pd.DataFrame({
        "date": pd.to_datetime(["2026-09-05", "2026-09-06", "2026-09-07", "2026-09-08"]),
        "amount": [500.0, 700.0, 300.0, 50.0],
        "description": ["HAVALE 1111111111 fatura", "TOROS MAKINE SAN cari mahsuben", "EGE GIDA PAZ.", "BILINMEYEN GONDEREN"],
    })
    out, alloc, unmatched = reconcile(inv, pay)
    by_id = out.set_index("invoice_id")["open_amount"]
    assert by_id["A2"] == 0 and by_id["A1"] == 300 and by_id["B1"] == 500
    assert list(alloc["method"]) == ["exact", "fifo", "fifo"]
    assert len(unmatched) == 1 and unmatched.iloc[0]["amount"] == 50


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


def test_model_is_scored_against_baseline(full):
    bt = pipeline.backtest_model(full, AS_OF)
    assert bt["n"] > 50 and 0.5 <= bt["coverage_p10_p90"] <= 0.98
    assert bt["mae_model"] < bt["mae_baseline"] * 1.15


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


def test_small_dataset_uses_simple_model(full):
    small = observe(full, AS_OF).tail(60).reset_index(drop=True)
    res = pipeline.forecast(small, AS_OF, 0.0, pd.DataFrame({"date": [], "amount": []}), n_sims=200)
    assert res["simple_model"] and np.all(res["sim"].p10 <= res["sim"].p90)


def test_ingest_reports_missing_columns_and_defaults(tmp_path):
    from radar import ingest

    p = tmp_path / "f.csv"
    p.write_text("Fatura No;Cari;Tarih;Toplam\nA1;Deneme Ltd;05.09.2026;1.250,50\nA2;Deneme Ltd;;100\n", encoding="utf-8")
    inv, notes = ingest.load_invoices(p, default_terms=45)
    assert len(inv) == 1 and inv.at[0, "amount"] == 1250.50
    assert inv.at[0, "due_date"] == pd.Timestamp("2026-10-20") and len(notes) == 2
    p.write_text("Belge;Kime\nA1;X\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Eksik sütun"):
        ingest.load_invoices(p)


def test_disputed_and_promised_invoices(full):
    obs = observe(full, AS_OF)
    open_ids = obs.loc[obs["open_amount"] > 0].sort_values("due_date")["invoice_id"]
    disputed_id, promised_id = open_ids.iloc[-1], open_ids.iloc[0]      # en yeni ve en eski açık fatura
    obs["disputed"] = obs["invoice_id"] == disputed_id
    obs["promised_date"] = pd.NaT
    obs.loc[obs["invoice_id"] == promised_id, "promised_date"] = pd.Timestamp(AS_OF) + pd.Timedelta(days=20)
    res = pipeline.forecast(obs, AS_OF, 0.0, pd.DataFrame({"date": [], "amount": []}), n_sims=300,
                            include_projected=False)
    ranked = res["ranked"].set_index("invoice_id", drop=False)
    assert disputed_id not in ranked.index and res["disputed_total"] > 0
    assert ranked.at[promised_id, "stage"] == "soz" and not ranked.at[promised_id, "actionable"]
    assert actions.draft_message(ranked.loc[promised_id], "X") is None
    # Söz verilen fatura, söz tarihinden çok önce ödenmiş sayılmamalı.
    assert ranked.at[promised_id, "expected_pay_day"] >= 10


def test_payday_habit_detection():
    from radar.features import MONTH_END, next_payday, payday_habit

    def habit(dates):
        d = pd.to_datetime(dates)
        return payday_habit(d.day.to_numpy(), (d.days_in_month - d.day).to_numpy())

    mid = ["2026-01-15", "2026-02-16", "2026-03-15", "2026-04-14", "2026-05-15", "2026-06-15", "2026-07-03"]
    eom = ["2026-01-31", "2026-02-28", "2026-03-31", "2026-04-30", "2026-05-29", "2026-06-30"]
    spread = ["2026-01-03", "2026-02-09", "2026-03-14", "2026-04-20", "2026-05-25", "2026-06-28", "2026-07-06"]
    assert habit(mid) == 15 and habit(eom) == MONTH_END and habit(mid[:3]) == 0 and habit(spread) == 0
    assert next_payday(np.datetime64("2026-10-16"), 15) == np.datetime64("2026-11-15")
    assert next_payday(np.datetime64("2026-10-16"), MONTH_END) == np.datetime64("2026-10-31")


def test_message_praise_is_customer_specific():
    row = {"invoice_id": "A1", "customer_name": "X", "due_date": "2026-10-05", "open_amount": 100.0,
           "stage": "hatirlatma", "days_overdue": -4, "cust_on_time": 0.9, "cust_n_paid": 8}
    assert "teşekkür" in actions.draft_message(row, "S")["body"]
    assert "teşekkür" not in actions.draft_message(row | {"cust_on_time": 0.3}, "S")["body"]
    assert "teşekkür" not in actions.draft_message(row | {"cust_n_paid": 2}, "S")["body"]


def test_backtest_on_own_data(full):
    obs = observe(full, AS_OF)
    bt = pipeline.backtest_own(obs, AS_OF, origins=2)
    assert len(bt) == 2 and (bt["p10"] <= bt["p90"]).all() and bt["actual"].gt(0).all()
    recent = obs[obs["issue_date"] > pd.Timestamp(AS_OF) - pd.Timedelta(days=200)]
    assert pipeline.backtest_own(recent, AS_OF) is None


def test_store_persists_tables_and_events(full, tmp_path):
    from radar.store import Store

    obs = observe(full, AS_OF)
    store = Store(tmp_path / "radar.db")
    assert store.load("invoices") is None and store.rev == 0
    store.save("invoices", obs)
    store.set("opening", 1500.0)
    open_ids = list(obs.loc[obs["open_amount"] > 0].sort_values("due_date")["invoice_id"])
    a, b, c = open_ids[0], open_ids[1], open_ids[2]
    store.add_event(a, "dispute", "1", ts="2026-09-20")
    store.add_event(b, "promise", "2026-10-25", ts="2026-09-21")
    store.add_event(c, "message", "taslak metni", ts="2026-09-29")
    store.add_event(a, "dispute", "0", ts="2026-10-05")           # AS_OF'tan sonra: henüz geçerli değil

    again = Store(tmp_path / "radar.db")                           # yeniden açınca her şey yerinde
    inv = again.apply_events(again.load("invoices"), AS_OF).set_index("invoice_id")
    assert len(inv) == len(obs) and float(again.get("opening")) == 1500.0 and again.rev == store.rev > 0
    assert inv["issue_date"].dtype.kind == "M" and inv.at[a, "disputed"] and not inv.at[b, "disputed"]
    assert inv.at[b, "promised_date"] == pd.Timestamp("2026-10-25")
    assert inv.at[c, "last_contact"] == pd.Timestamp("2026-09-29")

    res = pipeline.forecast(inv.reset_index(), AS_OF, 0.0, pd.DataFrame({"date": [], "amount": []}),
                            n_sims=200, include_projected=False)
    ranked = res["ranked"].set_index("invoice_id")
    assert a not in ranked.index and ranked.at[b, "stage"] == "soz"
    assert not ranked.at[c, "actionable"]                          # 2 gün önce yazıldı, bekleme süresinde
    later = again.apply_events(again.load("invoices"), "2026-10-10").set_index("invoice_id")
    assert not later.at[a, "disputed"]


def test_manual_column_mapping(tmp_path):
    from radar import ingest

    p = tmp_path / "f.csv"
    p.write_text("Evrak;Kime Kesildi;Kesim Günü;Net\nA1;Deneme Ltd;05.09.2026;1.250,50\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Eksik sütun"):
        ingest.load_invoices(p)
    assert ingest.columns(p) == ["Evrak", "Kime Kesildi", "Kesim Günü", "Net"]
    mapping = {"invoice_id": "Evrak", "customer_name": "Kime Kesildi", "issue_date": "Kesim Günü", "amount": "Net"}
    inv, _ = ingest.load_invoices(p, mapping=mapping)
    assert inv.at[0, "invoice_id"] == "A1" and inv.at[0, "amount"] == 1250.50


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


def test_doubtful_receivables_are_separated():
    res = pipeline.demo(seed=7, as_of=AS_OF, n_sims=400)
    ranked = res["ranked"]
    doubtful = ranked[ranked["stage"] == "supheli"]
    assert len(doubtful) and not doubtful["actionable"].any()
    assert (doubtful["days_overdue"] > actions.DOUBTFUL_MIN_OVERDUE).all()
    assert (doubtful["p_collect"] < actions.DOUBTFUL_MAX_COLLECT_PROB).all()
    assert actions.draft_message(doubtful.iloc[0], "X") is None
    # Gerçekte de bunların çoğu sonradan tahsil edilememiş olmalı.
    truth = res["full"].set_index("invoice_id")["true_paid_date"].reindex(doubtful["invoice_id"])
    assert truth.isna().mean() > 0.7


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


def test_foreign_currency_and_refund_invoices_are_reported_not_mixed(tmp_path, full):
    from radar import ingest

    p = tmp_path / "f.csv"
    p.write_text("Fatura No;Cari;Tarih;Toplam;Para Birimi;Fatura Tipi\n"
                 "A1;Deneme Ltd;05.09.2026;1000;TL;SATIS\n"
                 "A2;Deneme Ltd;06.09.2026;500;USD;SATIS\n"
                 "A3;Deneme Ltd;07.09.2026;200;TRY;IADE\n"
                 "A4;Deneme Ltd;08.09.2026;300;;SATIS\n", encoding="utf-8")
    inv, notes = ingest.load_invoices(p)
    assert list(inv["invoice_id"]) == ["A1", "A4"] and inv["amount"].sum() == 1300
    assert any("USD" in n for n in notes) and any("iade" in n for n in notes)

    row = full.iloc[0]
    usd = to_ubl_xml(row).replace('currencyID="TRY"', 'currencyID="USD"')
    refund = to_ubl_xml(row).replace("<cbc:IssueDate>", "<cbc:InvoiceTypeCode>IADE</cbc:InvoiceTypeCode><cbc:IssueDate>")
    df, notes = ingest.load_ubl([usd.encode(), refund.encode()])
    assert df.empty and len(notes) == 2
    ok, notes = ingest.load_ubl([to_ubl_xml(row).encode()])
    assert len(ok) == 1 and not notes


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


def test_refunds_are_netted_and_currency_converted_with_given_rates(tmp_path):
    from radar import ingest

    p = tmp_path / "f.csv"
    p.write_text("Fatura No;Cari;Tarih;Vade;Toplam;Para Birimi;Fatura Tipi\n"
                 "A1;Deneme Ltd;01.08.2026;01.09.2026;1000;TL;SATIS\n"
                 "A2;Deneme Ltd;05.08.2026;05.09.2026;500;TL;SATIS\n"
                 "R1;Deneme Ltd;10.09.2026;;1200;TL;IADE\n"
                 "B1;Baska AS;02.08.2026;02.09.2026;100;USD;SATIS\n"
                 "B2;Baska AS;03.08.2026;03.09.2026;10;EUR;SATIS\n", encoding="utf-8")
    inv, notes = ingest.load_invoices(p, rates=ingest.parse_rates("usd = 40,5; GBP=yok"))
    by = inv.set_index("invoice_id")
    assert list(by.index) == ["A1", "B1", "A2"]                       # EUR kuru yok: dışarıda; iade satır değil
    assert by.at["A1", "open_amount"] == 0 and by.at["A2", "open_amount"] == 300      # 1200 TL iade, eskiden yeniye
    assert by.at["B1", "amount"] == pytest.approx(4050) and by.at["B1", "currency"] == "USD"
    assert sum("EUR" in n for n in notes) == 1 and any("USD = 40.5" in n for n in notes) and any("iade" in n for n in notes)
    assert ingest.parse_rates("") == {} and ingest.parse_rates("EUR=48,2\nusd=41") == {"EUR": 48.2, "USD": 41.0}


def test_mailer_sends_only_valid_complete_requests(monkeypatch):
    import smtplib

    from radar import mailer

    sent = []

    class FakeSMTP:
        def __init__(self, host, port, **kw):
            self.host, self.port = host, port
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def starttls(self, **kw): sent.append("tls")
        def login(self, user, password):
            if password == "yanlis":
                raise smtplib.SMTPAuthenticationError(535, b"bad")
        def send_message(self, msg): sent.append(msg)

    monkeypatch.setattr(smtplib, "SMTP", FakeSMTP)
    cfg = mailer.MailConfig("smtp.example.com", 587, "ben@example.com", "gizli")
    mailer.send(cfg, " musteri@firma.com.tr ", "Fatura hakkında", "Merhaba, ödeme hatırlatması.")
    assert sent[0] == "tls" and sent[1]["To"] == "musteri@firma.com.tr" and sent[1]["From"] == "ben@example.com"
    assert "ödeme hatırlatması" in sent[1].get_content()
    with pytest.raises(mailer.MailError, match="Alıcı"):
        mailer.send(cfg, "adres-degil", "k", "m")
    with pytest.raises(mailer.MailError, match="eksik"):
        mailer.send(mailer.MailConfig("smtp.example.com", 587, "ben@example.com", ""), "a@b.co", "k", "m")
    with pytest.raises(mailer.MailError, match="Giriş reddedildi"):
        mailer.send(mailer.MailConfig("smtp.example.com", 587, "ben@example.com", "yanlis"), "a@b.co", "k", "m")
    assert len(sent) == 3                                  # hatalı denemelerde hiçbir ileti gitmedi


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


def test_bank_statement_with_preamble_direction_and_rich_descriptions(tmp_path):
    from radar import ingest

    p = tmp_path / "ziraat.csv"
    p.write_text(
        "Hesap No;12345678\nIBAN;TR000000000000000000000000\nDönem;01.10.2026 - 31.10.2026\n\n"
        "İşlem Tarihi;Açıklama;İşlem Tutarı (TL);B/A;Bakiye (TL)\n"
        "05.10.2026;GELEN EFT - ÖRNEK LOJİSTİK A.Ş. - VKN:6480591234 - GIB2026000000142 NOLU FATURA;144.000,00;A;412.500,00\n"
        "07.10.2026;FAST GELEN - KUZEY YILDIZI MAKİNA SAN. LTD. ŞTİ. - SORGUNO:0482910;60.000,00;A;472.500,00\n"
        "09.10.2026;GİDEN EFT - MARMARA ENERJİ - EKİM;18.450,00;B;454.050,00\n"
        "10.10.2026;ÜYE İŞYERİ POS BLOKE ÇÖZÜMÜ;24.375,00;A;478.425,00\n", encoding="utf-8")
    pay, notes = ingest.load_payments(p)
    assert len(pay) == 3 and pay["amount"].sum() == 144000 + 60000 + 24375      # giden EFT düştü

    inv = pd.DataFrame({
        "invoice_id": ["GIB2026000000141", "GIB2026000000142", "K1", "K2"],
        "customer_id": ["6480591234", "6480591234", "K", "K"],
        "customer_name": ["Örnek Lojistik ve Depolama A.Ş.", "Örnek Lojistik ve Depolama A.Ş.",
                          "Kuzey Yıldızı Makina San. Ltd. Şti.", "Kuzey Yıldızı Makina San. Ltd. Şti."],
        "vkn": ["6480591234", "6480591234", "", ""],
        "due_date": pd.to_datetime(["2026-09-01", "2026-10-01", "2026-09-05", "2026-09-20"]),
        "open_amount": [50000.0, 144000.0, 40000.0, 40000.0]})
    out, alloc, unmatched = reconcile(inv, pay)
    by = out.set_index("invoice_id")["open_amount"]
    # Fatura numarası açıklamada geçtiği için daha eski fatura değil, adı geçen fatura kapandı.
    assert by["GIB2026000000142"] == 0 and by["GIB2026000000141"] == 50000
    assert by["K1"] == 0 and by["K2"] == 20000                                  # unvanla bulundu, FIFO
    assert list(alloc["method"])[:1] == ["fatura_no"] and len(unmatched) == 1   # POS satırı müşteriye bağlanmadı


def test_ambiguous_names_are_not_guessed():
    from radar.reconcile import identify_customer

    customers = pd.DataFrame({"customer_id": ["A", "B"], "vkn": ["", ""],
                              "customer_name": ["Anadolu Yapı Market A.Ş.", "Anadolu Yapı Malzeme Ltd. Şti."]})
    assert identify_customer("GELEN EFT ANADOLU YAPI", customers) is None
    assert identify_customer("GELEN EFT ANADOLU YAPI MARKET", customers) == "A"
    assert identify_customer("HAVALE VKN: 1234567890", customers.assign(vkn=["1234567890", ""])) == "A"


def test_mikro_series_number_phone_and_cheque_status(tmp_path):
    from radar import ingest

    p = tmp_path / "mikro.csv"
    p.write_text("Evrak Tarihi;Evrak Seri;Evrak Sıra;Cari İsmi;Vade Tarihi;Genel Toplam;Telefon\n"
                 "02.10.2026;MKR;2026000418;Ege Plastik Kalıp A.Ş.;01.12.2026;318.000,00;0532 123 45 67\n",
                 encoding="utf-8")
    inv, _ = ingest.load_invoices(p)
    assert inv.at[0, "invoice_id"] == "MKR2026000418" and inv.at[0, "phone"] == "905321234567"
    assert ingest.normalize_phone("5321234567") == "905321234567" and ingest.normalize_phone("0212 555 11 22") == ""

    c = tmp_path / "cek.csv"
    c.write_text("Vade;Tutar;Keşideci;Durum\n15.12.2026;200.000;Ege Plastik;Portföyde\n"
                 "20.12.2026;100.000;Bursa Oto;Tedarikçiye ciro edildi\n10.01.2027;50.000;Delta;Bankaya tahsile verildi\n"
                 "12.01.2027;70.000;Delta;Faktoringe iskonto\n", encoding="utf-8")
    chq, notes = ingest.load_cheques(c)
    assert list(chq["amount"]) == [200000, 50000] and "170,000" in notes[0]


def test_weekday_habit_and_whatsapp_link():
    from radar.actions import WEEKDAYS, payday_label, weekday_habit, whatsapp_link

    fridays = pd.date_range("2026-01-02", periods=8, freq="7D").dayofweek
    assert weekday_habit(fridays) == 4 and WEEKDAYS[4] == "Cuma" and payday_label(0, 4) == "her Cuma"
    assert weekday_habit(pd.date_range("2026-01-01", periods=10, freq="D").dayofweek) == -1
    link = whatsapp_link("905321234567", "Merhaba, 1.250,00 TL & fatura")
    assert link.startswith("https://wa.me/905321234567?text=Merhaba%2C%201.250%2C00%20TL%20%26")


def test_fixed_cost_plan_follows_tax_calendar():
    from radar.ingest import fixed_cost_plan

    plan = fixed_cost_plan("2026-10-14", 60, payroll=100, payroll_day=31, muhtasar=10, sgk=20, kdv=30)
    got = {(r.label, r.date.strftime("%d.%m")) for r in plan.itertuples()}
    assert ("Muhtasar", "26.10") in got and ("KDV", "28.10") in got
    assert ("SGK primi", "02.11") in got           # 31 Ekim 2026 Cumartesi -> Pazartesi
    assert ("KDV", "30.11") in got                  # 28 Kasım Cumartesi -> 30 Kasım Pazartesi
    assert ("Maaş", "31.10") in got and ("Maaş", "30.11") in got   # 31 olmayan ayda ay sonu


def test_dashboard_script_compiles():
    import ast
    from pathlib import Path

    ast.parse((Path(__file__).parents[1] / "app.py").read_text(encoding="utf-8"))


def test_ledger_import_mikro_style_with_cheque(tmp_path):
    from radar import ingest

    p = tmp_path / "mikro_foy.csv"
    p.write_text(
        "Evrak Tarihi;Evrak No;Evrak Tipi;Cari Kodu;Cari İsmi;Vade Tarihi;Açıklama;Borç;Alacak;Bakiye\n"
        "02.08.2026;MKR001;Satış Faturası;120.01;Ege Plastik A.Ş.;01.09.2026;Fatura;318.000,00;0;318.000,00\n"
        "15.08.2026;MKR002;Satış Faturası;120.01;Ege Plastik A.Ş.;14.09.2026;Fatura;100.000,00;0;418.000,00\n"
        "06.09.2026;CEK082;Çek Giriş Bordrosu;120.01;Ege Plastik A.Ş.;15.12.2026;Çek tahsilatı;0;200.000,00;218.000,00\n"
        "10.09.2026;EFT1;Havale;120.01;Ege Plastik A.Ş.;;Gelen EFT;0;150.000,00;68.000,00\n"
        "11.09.2026;MKR003;Satış Faturası;120.02;Bursa Oto Ltd.;;Fatura;50.000,00;0;50.000,00\n",
        encoding="utf-8")
    assert ingest.is_ledger(p)
    inv, notes, chq = ingest.load_ledger(p, default_terms=30)
    by = inv.set_index("invoice_id")
    # 200.000 çek + 150.000 havale en eski faturadan başlayarak kapatır: MKR001 kapanır, MKR002'de 68.000 kalır.
    assert by.at["MKR001", "open_amount"] == 0 and by.at["MKR001", "paid_date"] == pd.Timestamp("2026-09-10")
    assert by.at["MKR002", "open_amount"] == 68000 and by.at["MKR003", "open_amount"] == 50000
    assert by.at["MKR003", "due_date"] == pd.Timestamp("2026-10-11")              # vade yok: +30 gün
    assert list(chq["amount"]) == [200000] and chq.at[0, "date"] == pd.Timestamp("2026-12-15")
    assert any("çek" in n for n in notes)


def test_ledger_single_customer_bizimhesap_style(tmp_path):
    from radar import ingest

    p = tmp_path / "Delta Elektrik.csv"
    p.write_text("Tarih;Belge Numarası;Vade Tarihi;Açıklama (İşlem Türü);Borç (TL);Alacak (TL);Bakiye (TL);B/A\n"
                 "01.10.2026;BZH512;31.10.2026;Mal Satış Faturası;96.000,00;0,00;96.000,00;B\n"
                 "09.10.2026;EFT-948;09.10.2026;Banka Havale Tahsilatı;0,00;146.000,00;-50.000,00;A\n", encoding="utf-8")
    with pytest.raises(ValueError, match="müşteri"):
        ingest.load_ledger(p)
    inv, notes, chq = ingest.load_ledger(p, fallback_customer="Delta Elektrik")
    assert inv.at[0, "open_amount"] == 0 and inv.at[0, "customer_name"] == "Delta Elektrik" and chq.empty
    assert any("50,000.00" in n for n in notes)                                    # fazla ödeme bildirildi


def test_sample_ledger_reproduces_open_receivables(tmp_path):
    from radar import ingest
    from radar.synthetic import export_samples

    export_samples(tmp_path, seed=3, as_of=AS_OF)
    inv, notes, chq = ingest.load_ledger(tmp_path / "cari_ekstre.csv")
    truth = observe(generate(seed=3, as_of=AS_OF), AS_OF)
    assert len(inv) == len(truth) and inv["open_amount"].sum() == pytest.approx(truth["open_amount"].sum(), rel=1e-6)


def test_sender_alias_memory_matches_unknown_sender():
    from radar.reconcile import sender_key

    inv = pd.DataFrame({"invoice_id": ["A1"], "customer_id": ["C1"], "customer_name": ["Yıldız Tekstil A.Ş."],
                        "vkn": [""], "due_date": pd.to_datetime(["2026-09-01"]), "open_amount": [1000.0]})
    pay = pd.DataFrame({"date": pd.to_datetime(["2026-09-05"]), "amount": [1000.0],
                        "description": ["GELEN EFT - MEHMET KAYA - SORGUNO:1234 - CARI ODEME"]})
    _, _, unmatched = reconcile(inv, pay)
    assert len(unmatched) == 1
    key = sender_key(pay.at[0, "description"])
    assert key == "mehmet kaya"
    out, alloc, unmatched = reconcile(inv, pay, aliases={key: "C1", "baska kisi": "YOK"})
    assert out.at[0, "open_amount"] == 0 and len(unmatched) == 0


def test_concentration_measures():
    from radar.actions import concentration

    obs = pd.DataFrame({"customer_name": ["A", "B", "C", "D"], "open_amount": [700.0, 100.0, 100.0, 100.0]})
    c = concentration(obs)
    assert c["top_share"] == pytest.approx(0.9) and c["top_names"][0] == "A"
    assert c["hhi"] == pytest.approx(0.52) and c["effective_n"] == pytest.approx(1 / 0.52)


def test_excel_damage_repairs_and_luca_account_names(tmp_path):
    from radar import ingest

    p = tmp_path / "luca.csv"
    p.write_text("Evrak Tarihi;Evrak No;Hesap Adı;VKN;Tutar;Döviz\n"
                 "03.10.2026;E1;120.01.0012 Trakya Tarım Ürünleri Paz. Ltd. Şti.;540123987;108.000,00;TRL\n"
                 "04.10.2026;E2;120.01.0034 - Başkent Medikal A.Ş.;1920384756.0;72.000,00;TL\n", encoding="utf-8")
    inv, notes = ingest.load_invoices(p)
    assert list(inv["vkn"]) == ["0540123987", "1920384756"] and not any("atlandı" in n for n in notes)
    assert list(inv["customer_name"]) == ["Trakya Tarım Ürünleri Paz. Ltd. Şti.", "Başkent Medikal A.Ş."]


def test_iban_alias_and_payment_instructions():
    from radar.actions import draft_message
    from radar.reconcile import sender_key

    desc = "FAST GELEN - AHMET YILMAZ - TR440001000482910482910001 - CARI ODEME"
    assert sender_key(desc) == "iban:TR440001000482910482910001"
    inv = pd.DataFrame({"invoice_id": ["A1"], "customer_id": ["C1"], "customer_name": ["Yılmaz Mühendislik"],
                        "vkn": [""], "due_date": pd.to_datetime(["2026-09-01"]), "open_amount": [500.0]})
    pay = pd.DataFrame({"date": pd.to_datetime(["2026-10-07"]), "amount": [500.0],
                        "description": ["FAST GELEN - A. YILMAZ - TR44 0001 0004 8291 0482 9100 01"]})
    out, _, unmatched = reconcile(inv, pay, aliases={sender_key(desc): "C1"})
    assert out.at[0, "open_amount"] == 0 and len(unmatched) == 0             # yazım farklı, IBAN aynı

    row = {"invoice_id": "GIB2026000000142", "customer_name": "X", "due_date": "2026-10-05", "open_amount": 100.0,
           "stage": "mutabakat", "days_overdue": 5}
    body = draft_message(row, "S", "TR12 3456", "Ziraat")["body"]
    assert "TR12 3456 (Ziraat) hesabımıza, açıklamaya GIB2026000000142 yazarak" in body
    assert "hesabımıza" not in draft_message(row, "S")["body"]


def test_security_hardening(tmp_path, monkeypatch):
    import tomllib

    from radar import ubl
    from radar.store import Store, default_path

    cfg = tomllib.loads((Path(__file__).parents[1] / ".streamlit" / "config.toml").read_text(encoding="utf-8"))
    assert cfg["server"]["address"] == "127.0.0.1" and cfg["browser"]["gatherUsageStats"] is False

    bomb = """<?xml version="1.0"?><!DOCTYPE x [<!ENTITY a "aaaaaaaaaa"><!ENTITY b "&a;&a;&a;&a;&a;&a;&a;&a;&a;&a;">]>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2">&b;</Invoice>"""
    with pytest.raises(Exception, match="(?i)entit"):
        ubl.parse_invoice(bomb)

    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.delenv("RADAR_DB", raising=False)
    assert default_path() == tmp_path / "KobiRadar" / "radar.db"
    store = Store(tmp_path / "x.db")
    with pytest.raises(ValueError):
        store.load("invoices; DROP TABLE settings")
    with pytest.raises(ValueError):
        store.add_event("A1", "hack")


def test_mail_headers_cannot_be_injected(monkeypatch):
    import smtplib

    from radar import mailer

    sent = []

    class FakeSMTP:
        def __init__(self, *a, **kw): pass
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def starttls(self, **kw): pass
        def login(self, *a): pass
        def send_message(self, msg): sent.append(msg)

    monkeypatch.setattr(smtplib, "SMTP", FakeSMTP)
    cfg = mailer.MailConfig("smtp.example.com", 587, "ben@example.com", "x")
    mailer.send(cfg, "a@b.co", "Fatura A1\nBcc: kurban@example.com", "metin")
    assert sent[0]["Bcc"] is None and "\n" not in sent[0]["Subject"]


def test_dashboard_renders_demo_and_own_data_without_errors(tmp_path, monkeypatch):
    """Panelin kendisini çalıştırır; bütün sekmeler aynı anda çizildiği için tablo ve grafik hataları burada çıkar."""
    import datetime

    from streamlit.testing.v1 import AppTest

    from radar import ingest
    from radar.store import Store

    root = Path(__file__).parents[1]
    monkeypatch.chdir(root)
    db = tmp_path / "panel.db"
    monkeypatch.setenv("RADAR_DB", str(db))
    store = Store(db)
    store.save("invoices", ingest.load_invoices(root / "ornekler" / "faturalar.csv")[0])
    store.save("payments", ingest.load_payments(root / "ornekler" / "ekstre.csv")[0])
    store.save("outflows", ingest.load_schedule(root / "ornekler" / "giderler.csv"))
    store.set("pilot_on", 1)                                              # pilot kayıtları bölümü de çizilsin
    store.set("sector", "46")                                             # TCMB sektör karşılaştırması da çizilsin
    store.add_pilot_record("2026-09-01", pd.DataFrame({
        "horizon": [14, 30], "until": ["2026-09-15", "2026-10-01"], "p10": [1e5, 2e5], "p50": [2e5, 4e5],
        "p90": [3e5, 6e5], "naive_due": [5e5, 7e5], "naive_median": [4e5, 6e5], "naive_rate": [2e5, 4e5]}))

    at = AppTest.from_file(str(root / "app.py"), default_timeout=300).run()
    assert not at.exception, [e.value for e in at.exception]
    assert len(at.metric) == 5 and at.metric[0].value.endswith("TL") and "," in at.metric[0].value
    at.sidebar.radio[0].set_value("Kendi verim").run()
    at.sidebar.date_input[0].set_value(datetime.date(2026, 10, 1)).run()
    assert not at.exception, [e.value for e in at.exception]
    assert len(at.dataframe) >= 1 and len(at.text_area) == 1
    assert not any("en son hareket" in e.value for e in at.error)
    assert any("Ortalama tahsil süreniz" in i.value for i in at.info)
    next(b for b in at.button if b.label == "Geri testi çalıştır").click().run()
    assert not at.exception, [e.value for e in at.exception]
    assert any("Basel Komitesi trafik ışığı" in m.value for m in at.markdown)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))                   # anonimleştirme anahtarı testte buraya
    next(b for b in at.sidebar.button if b.label == "Takma adlı paketi hazırla").click().run()
    assert not at.exception, [e.value for e in at.exception]
    next(b for b in at.button if b.label == "Pilot raporunu hazırla").click().run()
    assert not at.exception, [e.value for e in at.exception]
    assert (tmp_path / "KobiRadar" / "anonim_anahtar.txt").exists()
    # Mali müşavir modu: yeni işletme eklenince boş bir işletmeye geçilir; eskisine dönülünce veri yerinde.
    at.sidebar.text_input(key="new_business").set_value("Deneme Ltd.").run()
    next(b for b in at.sidebar.button if b.label == "Ekle").click().run()
    assert not at.exception, [e.value for e in at.exception]
    assert at.session_state["active_business"] == "Deneme Ltd." and len(at.metric) == 0
    at.sidebar.selectbox[0].set_value("İşletmem").run()
    assert not at.exception and len(at.metric) == 9              # 5 özet + 4 veri kalitesi
    # Tanıtım için örnek işletme: bugünün tarihli uydurma veriyle dolu, eski veri uyarısı yok.
    next(b for b in at.sidebar.button if b.label == "Tanıtım için örnek işletme ekle").click().run()
    assert not at.exception, [e.value for e in at.exception]
    assert at.session_state["active_business"] == "Örnek İşletme (uydurma veri)" and len(at.metric) == 9
    assert not any("en son hareket" in e.value for e in at.error)
    at.sidebar.selectbox[0].set_value("İşletmem").run()
    at.sidebar.date_input[0].set_value(datetime.date(2026, 10, 20)).run()
    assert any("en son hareket" in e.value for e in at.error)             # 19 gün eski veri uyarısı


def test_upload_undo_and_backup(tmp_path):
    import sqlite3

    from radar.store import Store

    store = Store(tmp_path / "s.db")
    store.save("invoices", pd.DataFrame({"invoice_id": ["A"], "amount": [1.0]}))
    assert not store.can_undo("invoices")
    store.save("invoices", pd.DataFrame({"invoice_id": ["B", "C"], "amount": [2.0, 3.0]}))
    assert store.can_undo("invoices") and list(store.load("invoices")["invoice_id"]) == ["B", "C"]
    store.undo("invoices")
    assert list(store.load("invoices")["invoice_id"]) == ["A"] and not store.can_undo("invoices")
    copy = tmp_path / "yedek.db"
    copy.write_bytes(store.backup_bytes())
    assert sqlite3.connect(copy).execute("SELECT invoice_id FROM invoices").fetchall() == [("A",)]


def test_weekly_plan_adds_up():
    res = pipeline.demo(seed=7, as_of=AS_OF, n_sims=300)
    week = pipeline.weekly_table(res)
    assert len(week) == 13 and week["Hafta"].iloc[0].startswith("02.10")
    out = res["outflows"]
    off = (out["date"] - pd.Timestamp(AS_OF)).dt.days
    assert week["Bilinen çıkışlar (TL)"].sum() == pytest.approx(out.loc[(off >= 1) & (off <= 91), "amount"].sum())
    assert (week["Hafta sonu kasa, kötümser (TL)"] <= week["Hafta sonu kasa, orta (P50) (TL)"]).all()
    assert week["Eksiye düşme olasılığı"].between(0, 1).all()


def test_message_outcomes_and_backtest_baselines(full):
    from radar.actions import message_outcomes

    obs = observe(full, AS_OF)
    paid = obs.dropna(subset=["paid_date"]).iloc[-1]
    open_ = obs[obs["paid_date"].isna()].iloc[0]
    events = pd.DataFrame({"ts": [paid["paid_date"] - pd.Timedelta(days=5), pd.Timestamp(AS_OF) - pd.Timedelta(days=30)],
                           "invoice_id": [paid["invoice_id"], open_["invoice_id"]], "kind": ["message", "message"],
                           "value": ["", ""]})
    out = message_outcomes(events, obs, AS_OF).set_index("Fatura")
    assert out.at[paid["invoice_id"], "Mesajdan sonra (gün)"] == 5
    assert out.at[paid["invoice_id"], "Durum"] == "14 gün içinde ödendi"
    assert out.at[open_["invoice_id"], "Durum"] == "14 günden uzun süredir açık"

    bt = pipeline.backtest_own(obs, AS_OF, origins=2)
    assert {"naive_due", "naive_median", "naive_rate", "err_due_pct", "err_median_pct", "err_rate_pct"} <= set(bt.columns)
    assert bt["err_p50_pct"].abs().mean() < bt["err_due_pct"].abs().mean()


def test_open_data_loaders_and_study_on_schema_replicas(tmp_path, full):
    """Gerçek açık veri setlerinin sütun düzeninde üretilmiş dosyalarla yükleyici ve çalışma sınanır."""
    from radar import open_data

    obs = observe(full, AS_OF).dropna(subset=["paid_date"])
    ibm = pd.DataFrame({"countryCode": "391", "customerID": obs["customer_id"], "PaperlessDate": "",
                        "invoiceNumber": obs["invoice_id"], "InvoiceDate": obs["issue_date"].dt.strftime("%m/%d/%Y"),
                        "DueDate": obs["due_date"].dt.strftime("%m/%d/%Y"), "InvoiceAmount": obs["amount"].round(2),
                        "Disputed": "No", "SettledDate": obs["paid_date"].dt.strftime("%m/%d/%Y"),
                        "PaperlessBill": "Paper", "DaysToSettle": 0, "DaysLate": 0})
    ibm.to_csv(tmp_path / "ibm.csv", index=False)
    a = open_data.load_ibm(tmp_path / "ibm.csv")
    assert len(a) == len(obs) and a["paid_date"].notna().all() and (a["due_date"] >= a["issue_date"]).all()

    pdd = pd.DataFrame({"business_code": "U001", "cust_number": obs["customer_id"], "name_customer": obs["customer_name"],
                        "clear_date": obs["paid_date"].dt.strftime("%Y-%m-%d 00:00:00"), "buisness_year": "2020.0",
                        "doc_id": obs["invoice_id"].str[3:] + ".0", "posting_date": obs["issue_date"].dt.strftime("%Y-%m-%d"),
                        "due_in_date": obs["due_date"].dt.strftime("%Y%m%d") + ".0", "invoice_currency": "USD",
                        "total_open_amount": obs["amount"].round(2), "invoice_id": obs["invoice_id"].str[3:] + ".0",
                        "isOpen": 0})
    pdd.to_csv(tmp_path / "pd.csv", index=False)
    b = open_data.load_payment_date(tmp_path / "pd.csv", max_per_customer=None)
    assert len(b) == len(obs) and b["due_date"].notna().all()

    study = open_data.delay_study(a, origins=3)
    assert len(study) >= 2 and {"mae_model", "mae_medyan", "mae_son2", "mae_son4", "mae_vade"} <= set(study.columns)
    assert study["kapsama_p10_p90"].between(0, 1).all()


def test_subset_sum_closes_the_invoices_actually_paid():
    from radar.reconcile import subset_match

    inv = pd.DataFrame({"invoice_id": ["A1", "A2", "A3", "A4"], "customer_id": "A",
                        "customer_name": "Toros Makine Sanayi A.Ş.", "vkn": "1111111111",
                        "due_date": pd.to_datetime(["2026-08-01", "2026-08-10", "2026-08-20", "2026-09-01"]),
                        "open_amount": [100.0, 250.0, 400.0, 75.0]})
    pay = pd.DataFrame({"date": pd.to_datetime(["2026-09-05"]), "amount": [475.0],
                        "description": ["HAVALE 1111111111 iki fatura"]})
    out, alloc, _ = reconcile(inv, pay)
    by = out.set_index("invoice_id")["open_amount"]
    # 475 = 400 + 75 tek çözüm: eski faturalar (A1, A2) değil, gerçekten ödenen A3 ve A4 kapanır.
    assert by["A3"] == 0 and by["A4"] == 0 and by["A1"] == 100 and by["A2"] == 250
    assert set(alloc["method"]) == {"toplu"}
    amounts = pd.Series([100.0, 200.0, 300.0])
    assert subset_match(amounts, 300.0) == [0, 1]          # yalnızca 2+ faturalık toplamlar aranır; tekli eşleşmeye reconcile önce bakar
    assert subset_match(pd.Series([100.0, 200.0, 150.0, 150.0]), 300.0) is None   # iki farklı çözüm: belirsiz, tahmin yok


def test_anonymized_package_hides_identities_and_keeps_the_numbers(tmp_path):
    import io
    import zipfile

    from radar import anonymize, ingest

    from radar.synthetic import export_samples
    export_samples(tmp_path, seed=3, as_of=AS_OF)
    inv, _ = ingest.load_invoices(tmp_path / "faturalar.csv")
    pay, _ = ingest.load_payments(tmp_path / "ekstre.csv")
    chq, _ = ingest.load_cheques(tmp_path / "cekler.csv")
    # Cari ekstreden gelen numarasız satırda kimlik müşteri adından üretilir; pakete sızmamalı.
    inv.loc[0, "invoice_id"] = "CARI-" + inv.loc[0, "customer_name"].upper().replace(" ", "")[:20] + "-20260101-0"
    inv.loc[1, "invoice_id"] = "KZY2024000000123"                       # GİB biçiminde numara, açıklamada geçiyor
    pay.loc[0, "description"] = "GELEN HAVALE KZY2024000000123 ÖDEMESİ"
    out = ingest.load_schedule(tmp_path / "giderler.csv")
    key = anonymize.load_or_create_key(tmp_path / "anahtar.txt")
    assert anonymize.load_or_create_key(tmp_path / "anahtar.txt") == key          # anahtar kalıcı
    blob, summary = anonymize.package("Örnek Ticaret A.Ş.", inv, key, pay, {"giderler": out, "cekler": chq})

    z = zipfile.ZipFile(io.BytesIO(blob))
    text = "\n".join(z.read(n).decode("utf-8-sig") for n in z.namelist())
    for name in inv["customer_name"].unique()[:10]:
        assert name not in text                                                  # gerçek unvan yok
    for vkn in inv["vkn"].unique()[:10]:
        assert vkn not in text                                                   # gerçek VKN yok
    assert "Örnek Ticaret" not in text and "GELEN HAVALE" not in text and "CARI-" not in text
    for number in inv["invoice_id"]:
        assert number not in text                                                # gerçek fatura no yok

    folder = tmp_path / "anon"
    z.extractall(folder)
    firm = next(folder.iterdir())
    a_inv, _ = ingest.load_invoices(firm / "faturalar.csv")
    a_pay, _ = ingest.load_payments(firm / "ekstre.csv")
    rec, _, unmatched = reconcile(a_inv.assign(open_amount=a_inv["amount"], paid_date=pd.NaT), a_pay)
    truth, _, truth_unmatched = reconcile(inv, pay)
    # Anonim veriden hesaplanan açık alacak ve eşleşmeyen tahsilatlar, gerçek veridekiyle aynı.
    assert rec["open_amount"].sum() == pytest.approx(truth["open_amount"].sum(), rel=1e-6)
    assert len(unmatched) == len(truth_unmatched)
    assert "KZY2024000000123" not in text and a_pay.loc[0, "description"].endswith(a_inv.loc[1, "invoice_id"])
    assert anonymize.pseudonym(key, "X") == anonymize.pseudonym(key, "X") != anonymize.pseudonym("başka", "X")
    assert anonymize._safe_label("Maaş ödemesi") == "Maaş" and anonymize._safe_label("Ahmet Yılmaz kira") == "Kira"
    assert anonymize._safe_label("Ahmet Yılmaz") == "Diğer"
    # Ek dosyalar panelin okuyucularıyla yeniden okunabiliyor; keşideci adı kalmıyor.
    a_chq, _ = ingest.load_cheques(firm / "cekler.csv")
    assert a_chq["amount"].sum() == pytest.approx(chq["amount"].sum()) and set(a_chq["label"]) <= {"Diğer", ""}
    assert ingest.load_schedule(firm / "giderler.csv")["amount"].sum() == pytest.approx(out["amount"].sum())


def test_pilot_report_builds_and_renders(tmp_path):
    from radar import pilot
    from radar.synthetic import cash_plan

    full = generate(seed=5, n_customers=20, as_of=AS_OF)
    obs = observe(full, AS_OF)
    opening, out = cash_plan(obs, AS_OF)
    r = pilot.build(obs, AS_OF, opening, out, label="Isletme_TEST")
    assert len(r["weeks"]) == 13 and not r["cash"].empty and not r["delays"].empty
    page = pilot.render(r)
    (tmp_path / "rapor.html").write_text(page, encoding="utf-8")
    assert page.startswith("<!doctype html>") and "<svg" in page and "Isletme_TEST" in page
    assert "http" not in page.split("</style>")[0]                     # dış kaynak yok
    import json
    every = json.loads(page.split('id="ileriye-donuk-kayit">')[1].split("</script>")[0])["record"]
    rec = [x for x in every if x["target"] == "tahsilat"]
    cash = [x for x in every if x["target"] == "kasa"]
    assert [x["horizon"] for x in rec] == [14, 30] and all(x["p10"] <= x["p50"] <= x["p90"] for x in rec)
    assert [x["horizon"] for x in cash] == [7, 14, 28] and cash[0]["naive_flat"] == round(opening)
    assert {"bant_genisligi_%", "aralik_skoru_%"} <= set(r["cash"].columns) and "orta tahmin (P50" in page
    assert rec[0]["naive_due"] <= rec[1]["naive_due"]                     # uzun ufukta en az o kadar tahsilat
    # Ufuk dolunca: kayıt, gerçekleşen veriyle (aynı şirketin 60 gün sonraki hâli) puanlanır.
    later = observe(generate(seed=5, n_customers=20, as_of=AS_OF), pd.Timestamp(AS_OF) + pd.Timedelta(days=60))
    detail, summary = pilot.score([pilot.read_record(page)], later)
    assert list(summary["ufuk_gun"]) == [14, 30] and (detail["gerceklesen"] > 0).all()
    assert {"B1", "B2", "dm_sonuc", "basel_alt", "fark_guven_araligi"} <= set(summary.columns) and set(summary["hedef"]) == {"tahsilat"}
    # B1: Diebold-Mariano (HLN) ile; kendi toleransımız yok.
    rng = np.random.default_rng(1)
    base = rng.uniform(80, 120, 20)
    errs = pd.DataFrame({"model": base * 0.6, "medyan": base, "oran": base * 1.1, "vade": base * 2})
    assert pilot.accuracy_test(errs, 2)["sonuc"] == "üstün"
    assert pilot.accuracy_test(errs.assign(model=base * 1.6), 2)["sonuc"] == "geride"
    assert pilot.accuracy_test(errs.assign(model=base * (1 + rng.normal(0, 0.05, 20))), 2)["sonuc"] == "eşdeğer"
    assert pilot.accuracy_test(errs.assign(medyan=np.nan, oran=np.nan), 2)["B1"] is None
    assert pilot.verdict(pd.DataFrame(), pd.DataFrame()).startswith("Geri test için yeterli geçmiş yok")
    assert "anlamlı biçimde daha" in pilot.verdict(None, pd.DataFrame({"dm_sonuc": ["üstün", "eşdeğer"]}))
    assert "geride" in pilot.verdict(None, pd.DataFrame({"dm_sonuc": ["üstün", "geride"]}))
    assert {"dm_sonuc", "basel_alt", "kupiec_p", "B1", "B2"} <= set(r["cash"].columns)
    hidden = pilot.render(pilot.build(obs, AS_OF, res=r["res"], label="X", key="gizli"))
    assert not any(name in hidden for name in r["top"]["Müşteri"])           # müşteri adları gizlendi
    assert not any(number in hidden for number in r["top"]["Fatura"])          # fatura numaraları da


def test_weekly_pilot_records_are_frozen_and_scheduled(tmp_path):
    from radar import pilot
    from radar.store import Store

    store = Store(tmp_path / "s.db")
    rec = pd.DataFrame({"horizon": [14, 30], "until": ["2026-10-29", "2026-11-14"], "p10": [1.0, 2.0],
                        "p50": [2.0, 3.0], "p90": [3.0, 4.0], "naive_due": [5.0, 6.0], "naive_median": [4.0, 5.0],
                        "naive_rate": [float("nan"), 2.5]})
    rev = store.rev
    assert store.add_pilot_record("2026-10-15", rec)
    assert not store.add_pilot_record("2026-10-15", rec.assign(p50=[99.0, 99.0]))       # dondurulmuş
    table = store.pilot_records()
    assert list(table["p50"]) == [2.0, 3.0] and table["naive_rate"].isna().iloc[0] and store.rev == rev
    store.clear()
    assert len(store.pilot_records()) == 2                                                # silme kayıtları korur

    today = pd.Timestamp("2026-10-15")
    assert pilot.record_due(table.iloc[:0], today, today, today=today) is None
    assert "bugün değil" in pilot.record_due(table.iloc[:0], "2026-10-01", today, today=today)
    assert "bir haftadan eski" in pilot.record_due(table.iloc[:0], today, "2026-10-01", today=today)
    assert "alındı" in pilot.record_due(table, "2026-10-20", "2026-10-20", today="2026-10-20")
    assert pilot.record_due(table, "2026-10-22", "2026-10-22", today="2026-10-22") is None
    records = pilot.records_from_table(table)
    assert records[0]["as_of"] == "2026-10-15" and len(records[0]["record"]) == 2


def test_accountant_mode_keeps_businesses_apart(tmp_path, monkeypatch):
    from radar import anonymize
    from radar.store import Store, create_business, list_businesses

    monkeypatch.setenv("RADAR_DB", str(tmp_path / "radar.db"))
    main = Store()
    main.save("invoices", pd.DataFrame({"invoice_id": ["A"], "amount": [1.0]}))
    assert list(list_businesses()) == ["İşletmem"]
    path = create_business("  Çağrı   Gıda Ltd. ")
    assert path.name == "cagri-gida-ltd.db" and list(list_businesses()) == ["İşletmem", "Çağrı Gıda Ltd."]
    with pytest.raises(ValueError):
        create_business("Çağrı Gıda Ltd.")
    other = Store(path)
    assert other.load("invoices") is None and other.name == "Çağrı Gıda Ltd."     # veriler ayrı
    assert main.business_id != other.business_id and Store().business_id == main.business_id   # kimlik kalıcı
    master = "m" * 64
    a, b = (anonymize.business_key(master, s.business_id) for s in (main, other))
    assert a != b and anonymize.pseudonym(a, "X") != anonymize.pseudonym(b, "X")      # işletmeler arası eşleşmez


def test_formal_draft_follows_lawyer_remarks():
    from radar import actions

    row = {"invoice_id": "ABC2026000000001", "customer_name": "X A.Ş.", "stage": "resmi", "due_date": "2026-08-01",
           "open_amount": 125000.0, "days_overdue": 75}
    d = actions.draft_message(row, "Örnek Ticaret A.Ş.")
    assert "%43" not in d["body"] and "2.020" not in d["body"] and "TCMB tarafından ilan edilen" in d["body"]
    assert "ihtarname" not in d["subject"].lower() and "TTK m. 1530 bilgilendirmesi" in d["subject"]
    assert "KEP veya Noter" in actions.FORMAL_NOTICE_WARNING


def test_partial_payments_and_closing_cash_are_scored_from_events():
    from radar import pilot
    from radar.reconcile import collection_events, reconcile

    inv = pd.DataFrame({"invoice_id": ["A", "B"], "customer_id": ["1", "1"], "customer_name": ["X A.Ş."] * 2,
                        "vkn": ["1234567890"] * 2, "issue_date": pd.to_datetime(["2026-09-01", "2026-09-05"]),
                        "due_date": pd.to_datetime(["2026-10-01", "2026-10-05"]), "amount": [1000.0, 500.0],
                        "open_amount": [1000.0, 500.0], "paid_date": pd.NaT})
    pay = pd.DataFrame({"date": pd.to_datetime(["2026-10-12", "2026-11-20"]), "amount": [400.0, 1100.0],
                        "description": ["X A.Ş. 1234567890 kısmi", "X A.Ş. 1234567890 kalan"]})
    paid, alloc, _ = reconcile(inv, pay)
    ev = collection_events(paid, alloc)
    assert ev["amount"].sum() == pytest.approx(1500.0) and len(ev) == 3            # 400 + 600 + 500
    # 10.10'da açık 1.500 TL; 14 gün içinde yalnızca 400 TL geldi. Fatura tutarı (1.000) değil, 400 sayılmalı.
    rec = {"as_of": "2026-10-10", "record": [{"target": "tahsilat", "horizon": 14, "until": "2026-10-24", "p10": 0,
                                              "p50": 500, "p90": 1500, "naive_due": 1500, "naive_median": 1000,
                                              "naive_rate": 700}]}
    detail, _ = pilot.score([rec], paid, events=ev)
    assert detail["gerceklesen"].iloc[0] == pytest.approx(400.0)
    # Kapanış kasası: 7 gün sonraki kayıtta girilen güncel kasa gerçekleşen sayılır.
    k1 = {"as_of": "2026-10-10", "opening": 1000.0, "meta": {"acilis_guncel": True},
          "record": [{"target": "kasa", "horizon": 7, "until": "2026-10-17", "p10": 800, "p50": 1200, "p90": 1500,
                      "naive_flat": 1000}]}
    k2 = {"as_of": "2026-10-17", "opening": 1300.0, "meta": {"acilis_guncel": True}, "record": []}
    detail, summary = pilot.score([k1, k2], paid, events=ev)
    row = summary[summary["hedef"] == "kasa"].iloc[0]
    assert detail.loc[detail["hedef"] == "kasa", "gerceklesen"].iloc[0] == 1300.0
    assert row["sapma_model_%"] < row["sapma_sabit_%"]                             # 100 TL'ye karşı 300 TL hata
    # Eşleşmesi düşük kayıt uyarılıdır ve tahsilat ölçümüne girmez.
    weak = {**rec, "meta": {"eslesme_orani": 0.5}}
    assert pilot.score([weak], paid, events=ev)[1].empty


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


def test_encrypted_backup_roundtrip_and_restore(tmp_path):
    from radar.store import Store, decrypt_backup, encrypt_backup

    store = Store(tmp_path / "a.db")
    store.save("invoices", pd.DataFrame({"invoice_id": ["A"], "amount": [1.0]}))
    store.set("seller", "Örnek A.Ş.")
    blob = encrypt_backup(store.backup_bytes(), "uzun-parola-1")
    assert "Örnek A.Ş.".encode() in store.backup_bytes() and "Örnek A.Ş.".encode() not in blob   # şifreli
    with pytest.raises(ValueError):
        decrypt_backup(blob, "yanlis-parola")
    with pytest.raises(ValueError):
        encrypt_backup(b"x", "kisa")
    other = Store(tmp_path / "b.db")
    other.save("invoices", pd.DataFrame({"invoice_id": ["Z", "Y"], "amount": [9.0, 8.0]}))
    safety = other.restore(blob, "uzun-parola-1")
    assert list(other.load("invoices")["invoice_id"]) == ["A"] and other.get("seller") == "Örnek A.Ş."
    assert safety.exists() and len(Store(safety).load("invoices")) == 2           # önceki veri kenarda
    with pytest.raises(ValueError):
        other.restore(b"rastgele bayt", None)


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
    assert list(exp["currency"]) == ["USD"] and exp["tl"].iloc[0] == pytest.approx(exp["original"].iloc[0] * 40.0)
    up = pipeline.fx_shift(res, 0.2)
    assert up["p10_min"] >= up["p10_min_before"] - 1e-6 and (up["p50"] >= res["sim"].p50 - 1e-6).all()


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


def test_standards_reproduce_basel_table_and_tests():
    from radar.standards import basel_zone, diebold_mariano, interval_report, kupiec_pof, passes

    # BCBS 1996, Tablo 2: 250 gözlem, %99 kapsama -> 0-4 yeşil, 5-9 sarı, 10+ kırmızı; 5 için P(X<=5) = %95,88.
    assert [basel_zone(250, x, 0.01)["zone"] for x in (4, 5, 9, 10)] == ["yeşil", "sarı", "sarı", "kırmızı"]
    assert basel_zone(250, 5, 0.01)["cum_prob"] == pytest.approx(0.9588, abs=1e-4)
    assert not kupiec_pof(250, 2, 0.01)["reject"] and kupiec_pof(384, 15, 0.10)["reject"]   # çok az aşım da kusur
    rep = interval_report(np.arange(100.0), np.arange(100.0) - 5, np.arange(100.0) + 5)
    assert rep["below"] == 0 and rep["kupiec_central"]["reject"] and not passes(rep)
    from radar.standards import spiegelhalter
    rng = np.random.default_rng(3)
    probs = rng.uniform(0, 1, 3000)
    assert not spiegelhalter(probs, rng.uniform(0, 1, 3000) < probs)["reject"]          # kalibre
    assert spiegelhalter(probs, rng.uniform(0, 1, 3000) < probs ** 0.5)["reject"]      # olasılıklar düşük
    d = diebold_mariano([1.0, 2, 3], [1.0, 2, 3])
    assert np.isnan(d["stat"])                                                     # 4'ten az gözlem


def test_audit_log_secure_delete_destroy_and_panel_password(tmp_path, monkeypatch):
    from radar import access
    from radar.store import Store

    monkeypatch.setenv("RADAR_DB", str(tmp_path / "radar.db"))
    store = Store(tmp_path / "radar.db")
    secret = "GIZLIMUSTERI-ABC-12345"
    store.save("invoices", pd.DataFrame({"invoice_id": ["A"], "customer_name": [secret], "amount": [1.0]}))
    store.clear()
    assert secret.encode() not in (tmp_path / "radar.db").read_bytes()          # silinen veri dosyada da yok
    log = store.audit_log()
    assert list(log["action"][:2]) == ["tablolar silindi", "dosya yüklendi"]
    (tmp_path / "radar.geri_yukleme_oncesi_20260101_000000.db").write_bytes(b"x")
    gone = store.destroy()
    assert len(gone) == 2 and not any(f.exists() for f in gone)
    assert not access.enabled() and access.check("ne olursa")
    with pytest.raises(ValueError):
        access.set_password("kisa")
    access.set_password("uzun-parola-9")
    assert access.enabled() and access.check("uzun-parola-9") and not access.check("yanlis-parola")
    assert "uzun-parola-9" not in access.password_file().read_text(encoding="utf-8")
    access.remove("uzun-parola-9")
    assert not access.enabled()


def test_panel_password_gate(tmp_path, monkeypatch):
    from streamlit.testing.v1 import AppTest

    from radar import access

    root = Path(__file__).parents[1]
    monkeypatch.chdir(root)
    monkeypatch.setenv("RADAR_DB", str(tmp_path / "panel.db"))
    access.set_password("dogru-parola-1")
    at = AppTest.from_file(str(root / "app.py"), default_timeout=300).run()
    assert len(at.metric) == 0 and at.text_input[0].label == "Panel parolası"
    at.text_input[0].set_value("yanlis-parola").run()
    at.button[0].click().run()
    assert any("Parola yanlış" in e.value for e in at.error) and len(at.metric) == 0
    at.text_input[0].set_value("dogru-parola-1").run()
    at.button[0].click().run()
    assert not at.exception and len(at.metric) == 5                       # demo şirket açıldı


def test_online_quantile_tracking_moves_each_tail_separately():
    from radar import pilot

    inv = pd.DataFrame({"invoice_id": [f"F{i}" for i in range(30)], "customer_id": "1", "customer_name": "X",
                        "issue_date": pd.Timestamp("2026-01-01"), "due_date": pd.Timestamp("2026-02-01"),
                        "amount": 100.0, "open_amount": 0.0,
                        "paid_date": [pd.Timestamp("2026-03-01") + pd.Timedelta(days=7 * i) for i in range(30)]})
    weeks = [pd.Timestamp("2026-02-20") + pd.Timedelta(days=7 * i) for i in range(20)]

    def table(lo, hi):
        return pd.DataFrame({"as_of": [f"{d:%Y-%m-%d}" for d in weeks], "target": "tahsilat", "horizon": 14,
                             "until": [f"{d + pd.Timedelta(days=14):%Y-%m-%d}" for d in weeks], "p10": lo, "p50": 150.0,
                             "p90": hi})
    # Her 14 günde ~200 TL geliyor. Bant çok yüksekte: hep kötümserin altında -> kötümser taraf genişler.
    low = pilot.online_adjustment(table(500.0, 900.0), inv)
    assert low["n"] > 10 and low["lo"] > 1.5 and low["hi"] == pytest.approx(1 - 0.1 * 0.1 * low["n"])   # aşımsız her kayıt -0,01
    # Bant çok aşağıda: hep iyimserin üstünde -> iyimser taraf genişler, kötümser 1'de kalır.
    high = pilot.online_adjustment(table(0.0, 50.0), inv)
    assert high["lo"] == 1.0 and high["hi"] > 1.5
    # Bant doğru: kötümser 1'in altına inmez (Basel ihtiyatı); kayıt yoksa ayar yok.
    ok = pilot.online_adjustment(table(0.0, 900.0), inv)
    assert ok["lo"] == 1.0 and pilot.online_adjustment(pd.DataFrame(), inv) == {"lo": 1.0, "hi": 1.0, "n": 0}


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


def test_sector_benchmark_from_tcmb_tables():
    from radar import benchmark

    b = benchmark.lookup("C", "kucuk")                                       # İmalat, küçük ölçek, 2025
    assert b["firma"] > 10000 and b["iyi_ceyrek_gun"] < b["medyan_gun"] < b["kotu_ceyrek_gun"]
    assert len(benchmark.sectors()) > 50 and benchmark.lookup("ZZ", "kucuk") is None
    assert "en iyi çeyrekte" in benchmark.compare(10, "C", "kucuk")
    assert "en kötü çeyrekte" in benchmark.compare(400, "C", "kucuk") and benchmark.compare(float("nan"), "C", "kucuk") is None


def test_scenario_lab_generator_split_and_source_anchors(tmp_path, monkeypatch):
    from radar import lab
    # Yeni boyutlar varsayılanda eski veriyi birebir üretir (eski testler ve sonuçlar geçerli kalır).
    a = generate(seed=4, n_customers=12, as_of=AS_OF)
    b = generate(seed=4, n_customers=12, as_of=AS_OF, season_amp=0.0, inflation=0.0, delay_scale=1.0,
                 terms_scale=1.0, size_sigma=0.6)
    pd.testing.assert_frame_equal(a, b)
    # Mevsimsellik tepe ayında satışı artırır, enflasyon eski faturaları ucuzlatır.
    s = generate(seed=4, n_customers=60, as_of=AS_OF, season_amp=0.4, season_peak=11)
    monthly = s.groupby(s["issue_date"].dt.month)["amount"].sum()
    assert monthly[11] > monthly[5]
    i = generate(seed=4, n_customers=12, as_of=AS_OF, inflation=0.5)
    assert i["amount"].iloc[:5].lt(a["amount"].iloc[:5]).all()

    dev, test = lab.sample("gelistirme", 30), lab.sample("sinav", 30)
    assert not set(dev["seed"]) & set(test["seed"])
    for name, (rng_dev, _, _) in lab.RANGES.items():
        assert dev[name].between(*rng_dev).all()
    held = test[test["saklı_boyut"] != ""]
    assert len(held) == 15 and all(
        lab.RANGES[r["saklı_boyut"]][1][0] <= r[r["saklı_boyut"]] <= lab.RANGES[r["saklı_boyut"]][1][1] for _, r in held.iterrows())
    assert dev["dso_hedef"].between(*lab.DSO_LIMITS).all()
    with pytest.raises(PermissionError):
        lab.run("sinav", 2)

    # Tahsil süresi sektör hedefine oturtulur ve küçük bir koşu raporlanır.
    row = dev.iloc[0].to_dict() | {"dso_hedef": 60.0}
    scale, achieved = lab.fit_delay_scale(row)
    assert abs(achieved - 60) / 60 < 0.15
    monkeypatch.setattr(lab, "LOG", tmp_path / "sinav_kaydi.csv")
    df = lab.run("sinav", 2, n_jobs=1, n_sims=200, confirm_test=True)
    assert (tmp_path / "sinav_kaydi.csv").exists() and df["seed"].nunique() == 2
    text = lab.report(df)
    assert "Zayıf bölgeler" in text and "Gerçekçilik denetimi" in text


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
