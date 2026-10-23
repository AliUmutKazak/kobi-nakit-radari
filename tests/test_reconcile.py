"""Banka tahsilatlarının faturalarla eşleştirilmesi."""

import numpy as np
import pandas as pd

from radar import pipeline
from radar.reconcile import reconcile
from radar.synthetic import generate, observe

from conftest import AS_OF


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


def test_ambiguous_names_are_not_guessed():
    from radar.reconcile import identify_customer

    customers = pd.DataFrame({"customer_id": ["A", "B"], "vkn": ["", ""],
                              "customer_name": ["Anadolu Yapı Market A.Ş.", "Anadolu Yapı Malzeme Ltd. Şti."]})
    assert identify_customer("GELEN EFT ANADOLU YAPI", customers) is None
    assert identify_customer("GELEN EFT ANADOLU YAPI MARKET", customers) == "A"
    assert identify_customer("HAVALE VKN: 1234567890", customers.assign(vkn=["1234567890", ""])) == "A"


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


def test_late_recorded_payments_are_not_counted_twice():
    from radar.simulate import snap_to_payday
    from radar.synthetic import cash_plan
    full = generate(seed=6, n_customers=40, as_of=AS_OF)
    # Tahsilatlar 12 gün geç işleniyor: kural son tahsilat gününü kesim sayar; günceldeyse bugünü.
    lagged = observe(full, AS_OF, record_lag=12)
    assert pipeline.payments_cutoff(lagged, AS_OF) <= pd.Timestamp(AS_OF) - pd.Timedelta(days=12)
    assert pipeline.payments_cutoff(observe(full, AS_OF), AS_OF) == pd.Timestamp(AS_OF)
    _, out = cash_plan(lagged, AS_OF)
    naive = pipeline.forecast(lagged, AS_OF, 0.0, out, n_sims=300)
    fixed = pipeline.forecast(lagged, AS_OF, 0.0, out, n_sims=300, payments_through=pipeline.payments_cutoff(lagged, AS_OF))
    # Arada ödenmiş olabilecek faturalar gelecek tahsilata eklenmez: orta tahmin daha düşük, gecikme bilgisi panelde.
    assert fixed["sim"].p50[-1] < naive["sim"].p50[-1] and fixed["info"]["payments_lag"] >= 12
    # Ödeme günü: ay sonu ödeyen müşteri ayın 1'inden sonra çekilen ödemeyi ay sonunda yapar; geçmişe gidilmez.
    assert list(snap_to_payday(np.array([-3, 5, 20]), 31, "2026-07-01", -6)) == [-1, -1, 30]
    assert list(snap_to_payday(np.array([0, 40]), 15, "2026-07-01", 1)) == [14, 45]


def test_bank_statement_direction_never_counts_outgoing_as_collection(tmp_path):
    from radar import ingest
    cases = {
        "isaretli.csv": ("Tarih;Açıklama;Tutar;Bakiye\n01.10.2026;GELEN HAVALE EGE;10.000,00;50.000,00\n"
                         "02.10.2026;KIRA;-15.000,00;35.000,00\n03.10.2026;SGK;-4.000,00;31.000,00\n"),
        "borc_alacak.csv": ("Tarih;Açıklama;Borç;Alacak;Bakiye\n01.10.2026;GELEN HAVALE;;10.000,00;50.000,00\n"
                            "02.10.2026;KIRA;15.000,00;;35.000,00\n03.10.2026;SGK;4.000,00;;31.000,00\n"),
        "bakiye.csv": ("Tarih;Açıklama;Tutar;Bakiye\n03.10.2026;SGK;4.000,00;31.000,00\n02.10.2026;KIRA;15.000,00;35.000,00\n"
                       "01.10.2026;GELEN HAVALE;10.000,00;50.000,00\n30.09.2026;ACILIS;1,00;40.000,00\n"),
    }
    for name, text in cases.items():
        (tmp_path / name).write_text(text, encoding="utf-8")
        ins, outs, _ = ingest.bank_movements(tmp_path / name)
        # Önceki sürümde işaretli ekstrede kira ve SGK (−15.000, −4.000) tahsilat sayılıyordu.
        assert list(ins["amount"]) == [10000.0] and sorted(outs["amount"]) == [4000.0, 15000.0], name
        # Ekstredeki son bakiye: dosya eskiden yeniye ya da yeniden eskiye sıralı olabilir.
        _, _, _, last = ingest.bank_movements(tmp_path / name, with_balance=True)
        if "Bakiye" in text:
            assert last == (pd.Timestamp("2026-10-03"), 31000.0), name
    (tmp_path / "yonsuz.csv").write_text("Tarih;Açıklama;Tutar\n01.10.2026;GELEN;10.000,00\n", encoding="utf-8")
    _, _, notes = ingest.bank_movements(tmp_path / "yonsuz.csv")
    assert any("giriş/çıkış ayrımı" in n for n in notes)
    assert ingest.bank_movements(tmp_path / "yonsuz.csv", with_balance=True)[3] is None
