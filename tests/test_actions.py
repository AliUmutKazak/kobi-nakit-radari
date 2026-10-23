"""Tahsilat önceliği, mesaj taslakları, itiraz ve ödeme sözü."""

import numpy as np
import pandas as pd
import pytest

from radar import actions, pipeline
from radar.synthetic import observe

from conftest import AS_OF


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


def test_weekday_habit_and_whatsapp_link():
    from radar.actions import WEEKDAYS, payday_label, weekday_habit, whatsapp_link

    fridays = pd.date_range("2026-01-02", periods=8, freq="7D").dayofweek
    assert weekday_habit(fridays) == 4 and WEEKDAYS[4] == "Cuma" and payday_label(0, 4) == "her Cuma"
    assert weekday_habit(pd.date_range("2026-01-01", periods=10, freq="D").dayofweek) == -1
    link = whatsapp_link("905321234567", "Merhaba, 1.250,00 TL & fatura")
    assert link.startswith("https://wa.me/905321234567?text=Merhaba%2C%201.250%2C00%20TL%20%26")


def test_concentration_measures():
    from radar.actions import concentration

    obs = pd.DataFrame({"customer_name": ["A", "B", "C", "D"], "open_amount": [700.0, 100.0, 100.0, 100.0]})
    c = concentration(obs)
    assert c["top_share"] == pytest.approx(0.9) and c["top_names"][0] == "A"
    assert c["hhi"] == pytest.approx(0.52) and c["effective_n"] == pytest.approx(1 / 0.52)


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


def test_formal_draft_follows_lawyer_remarks():
    from radar import actions

    row = {"invoice_id": "ABC2026000000001", "customer_name": "X A.Ş.", "stage": "resmi", "due_date": "2026-08-01",
           "open_amount": 125000.0, "days_overdue": 75}
    d = actions.draft_message(row, "Örnek Ticaret A.Ş.")
    assert "%43" not in d["body"] and "2.020" not in d["body"] and "TCMB tarafından ilan edilen" in d["body"]
    assert "ihtarname" not in d["subject"].lower() and "TTK m. 1530 bilgilendirmesi" in d["subject"]
    assert "KEP veya Noter" in actions.FORMAL_NOTICE_WARNING
    assert "asgari giderim tutarı" in d["body"] and "tazminat" not in d["body"]          # TTK m.1530/7 ifadesi
    # Ticari işletme olduğu anlaşılmayan müşteride (TCKN, şirket unvanı yok) TTK m.1530'a atıf yapılmaz.
    person = row | {"customer_name": "Ayşe Yılmaz", "vkn": "12345678901"}
    p = actions.draft_message(person, "Örnek Ticaret A.Ş.")
    assert "1530" not in p["body"] + p["subject"] and "faiz" not in p["body"] and "6502" in p["note"]
    assert actions.is_business({"vkn": "1234567890", "customer_name": "Ayşe Yılmaz"})


def test_sender_identity_follows_e_message_regulation():
    from radar import actions
    assert actions.sender_identity_problem("Örnek Ticaret A.Ş. (MERSİS 0123456789000015)") is None
    assert actions.sender_identity_problem("Ahmet Demir, VKN 1234567890") is None
    assert "MERSİS" in actions.sender_identity_problem("Örnek Ticaret A.Ş.")
    assert actions.sender_identity_problem("") and actions.sender_identity_problem("MERSİS 0123456789000015")


def test_promise_reliability_counts_kept_promises():
    from radar import actions
    obs = pd.DataFrame({"invoice_id": ["A", "B", "C"], "customer_name": ["X", "Y", "Y"],
                        "paid_date": pd.to_datetime(["2026-09-05", "2026-09-20", None])})
    ev = pd.DataFrame({"invoice_id": ["A", "B", "C", "A"], "kind": ["promise"] * 3 + ["message"],
                       "value": ["2026-09-06", "2026-09-10", "2026-09-15", ""],
                       "ts": pd.to_datetime(["2026-09-01"] * 4)})
    r = actions.promise_reliability(ev, obs, "2026-10-01")
    assert r["n"] == 3 and r["kept"] == 1 and r["broken_by_customer"] == {"Y": 2}
    assert actions.promise_reliability(ev, obs, "2026-09-01") is None              # tarihi geçmiş söz yok
