"""Pilot kayıtları, doğrulama standartları, açık veri ve Aşama 0."""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from radar.reconcile import reconcile
from radar.synthetic import generate, observe

from conftest import AS_OF


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
    # Kapsam: kasa tutarının tarihi, tahsilat kesimi, dahil ve dışarıda kalan kaynaklar her raporda yazılır.
    assert "Tahminin kapsamı" in page and "Hiçbir durumda dahil olmayan" in page and "kayıtlı değil" in page
    scoped = dict(r["res"], scope={"banka_ekstresi": True, "giderler": True, "odenecek_faturalar": False,
                                   "cekler": False, "yeni_satislar": True})
    cov = pilot.coverage_table(scoped, AS_OF, "2026-09-28")
    assert cov["Kasa ve banka tutarının girildiği gün"] == "28.09.2026 (tahmin tarihinden 3 gün önce)"
    assert cov["Yüklenmediği için dahil olmayan"] == "ödenecek faturalar, çek/senet portföyü"
    assert cov["Tahmine dahil kaynaklar"].startswith("açık faturalar, banka ekstresi")


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
    assert row["eksik_hafta"] == 0 and row["kasa_guncel_olmayan_kayit"] == 0
    k3 = {**k2, "as_of": "2026-10-31", "meta": {}}                                  # 24 Ekim haftası atlandı
    row = pilot.score([k1, k2, k3], paid, events=ev)[1].query("hedef == 'kasa'").iloc[0]
    assert row["eksik_hafta"] == 1 and row["kasa_guncel_olmayan_kayit"] == 1
    # Eşleşmesi düşük kayıt uyarılıdır ve tahsilat ölçümüne girmez.
    weak = {**rec, "meta": {"eslesme_orani": 0.5}}
    assert pilot.score([weak], paid, events=ev)[1].empty


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
    # Bant çok aşağıda: hep iyimserin üstünde -> iyimser taraf genişler, kötümser yavaşça daralır.
    high = pilot.online_adjustment(table(0.0, 50.0), inv)
    assert high["hi"] > 1.5 and high["lo"] == pytest.approx(1 - 0.01 * high["n"])
    # Aşım yoksa her kayıt katsayıyı yalnızca 0,01 daraltır; kayıt yoksa ayar yok.
    ok = pilot.online_adjustment(table(0.0, 900.0), inv)
    assert ok["lo"] == pytest.approx(1 - 0.01 * ok["n"]) and pilot.online_adjustment(pd.DataFrame(), inv) == {"lo": 1.0, "hi": 1.0, "n": 0}


@pytest.mark.skipif(not (Path(__file__).parents[1] / "src/radar/data/sektor_alacak_2025.csv").exists(),
                    reason="TCMB tablosu yeniden dağıtılamadığı için depoda yok")
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

    from radar import benchmark
    if not benchmark.available():
        pytest.skip("Senaryo laboratuvarı TCMB sektör tablosunu gerektirir; tablo depoda yok")
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


def test_sector_table_is_optional_for_distribution(monkeypatch, tmp_path):
    from radar import benchmark
    monkeypatch.setattr(benchmark, "TABLE", tmp_path / "yok.csv")
    assert not benchmark.available() and benchmark.compare(70, "C", "kucuk") is None


def test_online_tracking_converges_on_the_shown_band():
    from radar import pilot
    rng = np.random.default_rng(0)
    t0 = pd.Timestamp("2025-01-06")
    n = 300
    # Bant gerçek dağılımdan dar (P90 ham bantta ~%31 aşılır). Geri beslemeyle katsayı dengeye gelir:
    # N(100, 20) için doğru iyimser katsayı ~ 1,28 · 20 / 10 = 2,56; aşım oranı %10'a yaklaşır.
    recs = pd.DataFrame({"as_of": [t0 + pd.Timedelta(days=7 * i) for i in range(n)],
                         "until": [t0 + pd.Timedelta(days=7 * i + 7) for i in range(n)],
                         "p10": 90.0, "p50": 100.0, "p90": 110.0, "actual": rng.normal(100, 20, n)})
    state, band = pilot.track_quantiles(recs, recs["until"].max())
    assert 1.8 < state["hi"] < 3.4                      # eski (ham bantla) yöntemde ~6,5'e kadar büyürdü
    late = band.iloc[n // 2:]
    assert 0.04 < (late["actual"] > late["hi"]).mean() < 0.18


def test_retrospective_phase_uses_weekly_origins_and_reports_progress(full):
    from radar import pilot
    obs = observe(full, AS_OF)
    n = pilot.retro_origins(obs, AS_OF)
    assert 4 <= n <= pilot.RETRO_MAX_ORIGINS
    assert pilot.retrospective(obs[obs["issue_date"] >= "2026-03-01"], AS_OF) is None     # 7 aydan kısa geçmiş
    seen = []
    summary = pilot.cash_backtest(obs, AS_OF, origins=4, step=pilot.RETRO_STEP, progress=seen.append)
    assert seen == [0.25, 0.5, 0.75, 1.0] and set(summary["tahmin_tarihi_sayisi"]) == {4}
    r = pilot.build(obs, AS_OF, retro=summary)
    page = pilot.render(r)
    assert r["retro"] and "Aşama 0" in page and "Kupiec p" in page


def test_simple_method_replaces_model_where_retrospective_says_behind(full):
    from radar import pilot
    obs = observe(full, AS_OF)
    retro = pd.DataFrame({"ufuk_gun": [14, 30], "dm_sonuc": ["geride", "eşdeğer"], "sapma_model_%": [30.0, 10.0],
                          "sapma_medyan_%": [20.0, 12.0], "sapma_oran_%": [15.0, 11.0], "sapma_vade_%": [40.0, 50.0]})
    reps = pilot.simple_replacements(retro, obs, AS_OF)
    assert [r["ufuk_gun"] for r in reps] == [14] and reps[0]["yontem"] == "oran" and reps[0]["tutar"] >= 0
    assert pilot.simple_replacements(retro.assign(dm_sonuc="eşdeğer"), obs, AS_OF) == []


def test_retrospective_uses_same_definition_as_forward_record_for_cheque_payers():
    """Dış inceleme (21.10.2026): Aşama 0 çek ayarı açık ve olaysız çalışıyordu; çekli işletmede model tahsilatı
    çek vadesine kaydırıyor, gerçekleşen ise kapanışta sayılıyordu. Ölçülen etki (12 hafta, çek payı 0,5): 30 günde
    sapma %37'den %16'ya indi. Aynı tanımla çekli ve çeksiz işletmenin sonucu aynıdır (kapanış ölçülür)."""
    from radar import pilot
    kw = dict(origins=4, step=7)
    with_cheques = observe(generate(seed=11, as_of=AS_OF, cheque_share=0.5), AS_OF)
    without = observe(generate(seed=11, as_of=AS_OF, cheque_share=0.0), AS_OF)
    new = pilot.cash_backtest(with_cheques, AS_OF, **kw)
    old = pilot.cash_backtest(with_cheques, AS_OF, same_as_forward=False, **kw)
    ref = pilot.cash_backtest(without, AS_OF, **kw)
    assert np.allclose(new["sapma_model_%"], ref["sapma_model_%"])
    assert (old["sapma_model_%"] > new["sapma_model_%"] + 5).all()


def test_b1_is_a_non_inferiority_decision_with_prespecified_margin():
    from radar import pilot
    assert pilot.b1_decision((-6.0, -1.0), 4.0, False) == (True, "üstün")
    assert pilot.b1_decision((-2.0, 3.0), 4.0, False) == (True, "eşdeğer (marj içinde)")
    assert pilot.b1_decision((-2.0, 6.0), 4.0, False) == (False, "kanıtlanamadı")       # az kanıt "geçti" sayılmaz
    assert pilot.b1_decision((5.0, 9.0), 4.0, False)[1] == "geride (marjın dışında)"
    assert pilot.b1_decision((-2.0, 3.0), None, False) == (False, "kanıtlanamadı (marj belirlenemedi)")
    assert pilot.b1_decision((-6.0, -1.0), 4.0, True)[0] is False                      # vadesinde öder'den kötü
    # Marj: kontrolün (en iyi basit yöntem) "vadesinde öder"e üstünlüğünün %95 alt sınırının yarısı.
    rng = np.random.default_rng(0)
    actual = rng.uniform(80, 120, 20)
    g = pd.DataFrame({"origin": pd.date_range("2026-01-05", periods=20, freq="7D"), "actual": actual,
                      "naive_due": actual * 1.6, "naive_median": actual * rng.uniform(0.95, 1.05, 20),
                      "naive_rate": actual * 1.3})
    m = pilot.b1_margin(g, 14, 7)
    assert m["kontrol"] == "medyan" and 50 < m["m1"] < 60 and m["m2"] == pytest.approx(m["m1"] / 2)
    assert pilot.b1_margin(g.assign(naive_due=g["naive_median"]), 14, 7)["m2"] is None   # kontrolün etkisi yok


def test_pooled_b1_replaces_vote_counting():
    """Protokol 1.8: işletmelerin çoğu tek başına "kanıtlanamadı" çıkarken birleşik analiz karar verebilir."""
    from radar import pilot, standards
    # Tek başına geniş aralıklı ama tutarlı beş işletme: fark ~0, M1 ~10 puan.
    firms = pd.DataFrame({"ufuk_gun": [30] * 5, "fark_tahmin": [1.0, -2.0, 0.5, 2.0, -1.0], "fark_se": [2.0] * 5,
                          "m1_tahmin": [9.0, 11.0, 10.0, 12.0, 8.0], "m1_se": [2.0] * 5})
    alone = [pilot.b1_decision((d - 1.96 * 2, d + 1.96 * 2), 0.5 * (m - 1.96 * 2), False)[1]
             for d, m in zip(firms["fark_tahmin"], firms["m1_tahmin"])]
    assert alone.count("eşdeğer (marj içinde)") <= 2                         # oy sayımı: çoğunluk "geçmedi"
    pooled = pilot.pooled_b1(firms).iloc[0]
    assert pooled["isletme"] == 5 and pooled["B1"] and pooled["B1_sonuc"] == "eşdeğer (marj içinde)"
    # Gerçekten kötü model birleşik analizde de geçmez.
    worse = pilot.pooled_b1(firms.assign(fark_tahmin=firms["fark_tahmin"] + 15)).iloc[0]
    assert not worse["B1"]
    # HKSJ: heterojenlik yokken ölçek 1'in altına inmez (Röver vd. 2015); tek çalışmada normal aralık.
    re1 = standards.random_effects([2.0], [1.0])
    assert re1["k"] == 1 and re1["ci"] == pytest.approx((2 - 1.959964, 2 + 1.959964), abs=1e-4)
    same = standards.random_effects([1.0, 1.0, 1.0], [1.0, 1.0, 1.0])
    assert same["tau2"] == 0 and same["ci"][1] - same["ci"][0] > 2 * 1.96 / np.sqrt(3)


def test_pilot_data_chain_end_to_end_with_three_synthetic_firms(tmp_path):
    """Pilot veri zincirinin provası: her işletmede Aşama 0 ve haftalık ileriye dönük kayıtlar; takma adlı paket;
    Proje tarafında paketlerden işletme satırları ve birleşik karar (protokol 1.8). Gerçek veri gelmeden zincirin
    kopuk halkası kalmadığını gösterir."""
    import sys
    import zipfile

    from radar import anonymize, pilot
    from radar.store import Store

    root = Path(__file__).parents[1]
    sys.path.insert(0, str(root / "tools"))
    from pilot_birlesik import from_packages

    unpacked = tmp_path / "paketler"
    for seed in (21, 22, 23):
        full = generate(seed=seed, n_customers=20, months=18, as_of=AS_OF)
        now = observe(full, AS_OF)
        # Aşama 0 (testte 4 hafta) ve marj: ilk kayıttan önce dondurulur.
        retro = pilot.cash_backtest(now, pd.Timestamp(AS_OF) - pd.Timedelta(days=100), origins=4, step=7)
        margins = {"m2": {str(int(r["ufuk_gun"])): r["b1_m2"] for _, r in retro.iterrows() if pd.notna(r["b1_m2"])},
                   "m1": {str(int(r["ufuk_gun"])): r["b1_m1"] for _, r in retro.iterrows() if pd.notna(r["b1_m1"])}}
        # Haftalık ileriye dönük kayıtlar: o gün görülen veriyle; ufuklar AS_OF'tan önce doluyor.
        store = Store(tmp_path / f"firma{seed}.db")
        for k in range(10):                     # 30 günlük ufukta en az iki bağımsız blok (2 × 5 hafta)
            t = pd.Timestamp(AS_OF) - pd.Timedelta(days=100 - 7 * k)
            record = pilot.forward_record(observe(full, t), t, n_sims=300)
            store.add_pilot_record(t, record, meta={"acilis_guncel": False})
        blob, summary = anonymize.package(f"Firma {seed}", now, "test-anahtari", records=store.pilot_records(),
                                          retro=retro, margins=margins)
        assert "asama0" in summary and "b1_marj" in summary
        with zipfile.ZipFile(__import__("io").BytesIO(blob)) as z:
            names = z.namelist()
            assert any(n.endswith("asama0.csv") for n in names) and any(n.endswith("b1_marj.json") for n in names)
            z.extractall(unpacked)
    firms = from_packages(unpacked)
    assert firms["isletme"].nunique() == 3 and set(firms["ufuk_gun"]) == {14, 30}
    assert firms[["fark_tahmin", "fark_se", "m1_tahmin", "m1_se"]].notna().all().all()
    pooled = pilot.pooled_b1(firms)
    assert set(pooled["ufuk_gun"]) == {14, 30} and (pooled["isletme"] == 3).all()
    assert (pooled["yetersiz_kayitli_isletme"] == 0).all()
    # Az kayıtlı işletme sessizce düşmez, sayısı raporlanır.
    short = pilot.pooled_b1(firms.assign(fark_se=np.where(firms["isletme"] == firms["isletme"].iloc[0], np.nan,
                                                          firms["fark_se"])))
    assert (short["yetersiz_kayitli_isletme"] == 1).all() and (short["isletme"] == 2).all()
    assert pooled["B1_sonuc"].isin(["üstün", "eşdeğer (marj içinde)", "kanıtlanamadı",
                                    "kanıtlanamadı (marj belirlenemedi)", "geride (marjın dışında)"]).all()
    assert pooled["B2_kayit"].gt(0).all()
    # Pakette fatura numarası ya da müşteri adı yerine takma adlar var; Aşama 0 dosyası yalnızca toplu sayılar.
    a0 = pd.read_csv(next(unpacked.rglob("asama0.csv")))
    assert set(a0.columns) <= set(anonymize.RETRO_COLUMNS)
