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
    assert worse["fresh"]["z_shift"] > steady["fresh"]["z_shift"]


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
