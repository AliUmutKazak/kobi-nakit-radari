"""Panelin kendisi: derlenme, uçtan uca çizim, ECB kur güncellemesi."""
import json
from pathlib import Path

import pandas as pd
import pytest


def test_dashboard_script_compiles():
    import ast
    from pathlib import Path

    ast.parse((Path(__file__).parents[1] / "app.py").read_text(encoding="utf-8"))


def test_dashboard_renders_demo_and_own_data_without_errors(tmp_path, monkeypatch):
    """Panelin kendisini çalıştırır; bütün sekmeler aynı anda çizildiği için tablo ve grafik hataları burada çıkar."""
    import datetime

    from streamlit.testing.v1 import AppTest

    from radar import ingest
    from radar.store import Store

    root = Path(__file__).parents[1]
    monkeypatch.chdir(root)
    from radar import pilot as pilot_mod
    monkeypatch.setattr(pilot_mod, "RETRO_MAX_ORIGINS", 4)               # Aşama 0: testte 52 yerine 4 hafta
    db = tmp_path / "panel.db"
    monkeypatch.setenv("RADAR_DB", str(db))
    store = Store(db)
    store.save("invoices", ingest.load_invoices(root / "ornekler" / "faturalar.csv")[0])
    store.save("payments", ingest.load_payments(root / "ornekler" / "ekstre.csv")[0])
    store.save("outflows", ingest.load_schedule(root / "ornekler" / "giderler.csv"))
    borc = tmp_path / "borc.csv"                                          # dövizli borç ve kuru girilmemiş döviz
    borc.write_text("Fatura No;Tedarikçi;Vade Tarihi;Tutar;Para Birimi\n"
                    "B1;Ithalatci;20.10.2026;2.000,00;USD\nB2;Isvicre;25.10.2026;100,00;CHF\n", encoding="utf-8")
    pay, pay_notes = ingest.load_payables(borc, rates={"USD": 49.5})
    store.save("payables", pay)
    store.set("notes_payables", __import__("json").dumps(pay_notes, ensure_ascii=False))
    store.set("rates", "USD=41,50")                                       # eski kur: uyarı çıkmalı
    store.set("pilot_on", 1)                                              # pilot kayıtları bölümü de çizilsin
    store.set("sector", "46")                                             # TCMB sektör karşılaştırması da çizilsin
    store.add_pilot_record("2026-09-01", pd.DataFrame({
        "horizon": [14, 30], "until": ["2026-09-15", "2026-10-01"], "p10": [1e5, 2e5], "p50": [2e5, 4e5],
        "p90": [3e5, 6e5], "naive_due": [5e5, 7e5], "naive_median": [4e5, 6e5], "naive_rate": [2e5, 4e5]}))

    at = AppTest.from_file(str(root / "app.py"), default_timeout=300).run()
    assert not at.exception, [e.value for e in at.exception]
    assert len(at.metric) == 6 and at.metric[0].value.endswith("TL") and "," in at.metric[0].value
    at.sidebar.radio[0].set_value("Kendi verim").run()
    at.sidebar.date_input[0].set_value(datetime.date(2026, 10, 1)).run()
    assert not at.exception, [e.value for e in at.exception]
    assert len(at.dataframe) >= 1 and len(at.text_area) == 1
    assert not any("en son hareket" in e.value for e in at.error)
    from radar import benchmark
    if benchmark.available():                                             # TCMB tablosu yalnızca izinli kurulumda
        assert any("Ortalama tahsil süreniz" in i.value for i in at.info)
    assert any(w.value.startswith("DİKKAT") for w in at.warning)          # kuru girilmemiş dövizli borç
    assert any(h.value == "Kur değişirse" for h in at.subheader)
    stale = next(w.value for w in at.warning if "Girdiğiniz USD kuru" in w.value)
    assert "(41,50)" in stale and "yanlış çevrilir. " in stale and "bu fark, son" in stale   # noktalama bozulmaz
    # Kasa tutarı panel dışında değişirse (ör. yedekten geri yükleme) alan da güncellenir, eskisi geri yazılmaz.
    Store(db).set("opening", 123456.0)
    at.run()
    assert not at.exception, [e.value for e in at.exception]
    assert float(Store(db).get("opening")) == 123456.0
    assert any(n.value == 123456.0 for n in at.sidebar.number_input)
    next(b for b in at.button if b.label == "Geri testi çalıştır").click().run()
    assert not at.exception, [e.value for e in at.exception]
    assert any("Basel tipi trafik ışığı" in m.value for m in at.markdown)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))                   # anonimleştirme anahtarı testte buraya
    next(b for b in at.sidebar.button if b.label == "Takma adlı paketi hazırla").click().run()
    assert not at.exception, [e.value for e in at.exception]
    next(b for b in at.button if b.label.startswith("Aşama 0 testini çalıştır")).click().run()
    assert not at.exception, [e.value for e in at.exception]
    assert Store(db).get("retro_result") and "Aşama 0" in Store(db).audit_log()["action"].str.cat()
    col = "Diebold-Mariano: geride değil"
    table = next(d.value for d in at.dataframe if col in d.value.columns)
    assert set(table[col]) <= {"geçti", "kaldı", "değerlendirilemedi"}                 # kayıttan okununca da
    next(b for b in at.button if b.label == "Pilot raporunu hazırla").click().run()
    assert not at.exception, [e.value for e in at.exception]
    assert (tmp_path / "KobiRadar" / "anonim_anahtar.txt").exists()
    # Mali müşavir modu: yeni işletme eklenince boş bir işletmeye geçilir; eskisine dönülünce veri yerinde.
    assert json.loads(Store(db).get("portfolio_summary"))["ozet"]["risk"] >= 0          # portföy özeti yazıldı
    rev = Store(db).rev
    at.run()
    assert Store(db).rev == rev                                                        # özet önbelleği bozmaz
    at.sidebar.text_input(key="new_business").set_value("Deneme Ltd.").run()
    next(b for b in at.sidebar.button if b.label == "Ekle").click().run()
    assert not at.exception, [e.value for e in at.exception]
    assert at.session_state["active_business"] == "Deneme Ltd." and len(at.metric) == 0
    at.sidebar.selectbox[0].set_value("İşletmem").run()
    assert not at.exception and len(at.metric) == 10             # 6 özet + 4 veri kalitesi
    assert any(e.label.startswith("Mali müşavir görünümü") for e in at.expander)  # iki işletme: portföy tablosu
    # Tanıtım için örnek işletme: bugünün tarihli uydurma veriyle dolu, eski veri uyarısı yok.
    next(b for b in at.sidebar.button if b.label == "Tanıtım için örnek işletme ekle").click().run()
    assert not at.exception, [e.value for e in at.exception]
    assert at.session_state["active_business"] == "Örnek İşletme (uydurma veri)" and len(at.metric) == 10
    assert not any("en son hareket" in e.value for e in at.error)
    assert not any("hangi gün girildiği kayıtlı değil" in w.value for w in at.warning)   # tanıtımda yanlış uyarı yok
    at.sidebar.selectbox[0].set_value("İşletmem").run()
    at.sidebar.date_input[0].set_value(datetime.date(2026, 10, 20)).run()
    assert any("en son hareket" in e.value for e in at.error)             # 19 gün eski veri uyarısı


def test_ecb_update_is_validated_and_stored_locally(tmp_path, monkeypatch):
    import io
    import zipfile

    from radar import fx
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    fx.clear_cache()
    try:
        tab = pd.read_csv(fx.DATA, parse_dates=["date"]).set_index("date")
        fx.validate(tab)                                                   # paketteki tablo denetimden geçer
        bad = tab.copy()
        bad.iloc[-1, bad.columns.get_loc("USD")] *= 2                      # tek günde kur ikiye katlanmış
        with pytest.raises(ValueError):
            fx.validate(bad)
        # ECB biçiminde (euro bazlı) sahte bir dosya: bir gün sonrası eklenmiş
        ecb = pd.DataFrame({"Date": tab.index.strftime("%Y-%m-%d"), "TRY": tab["EUR"]})
        for c in fx.CURRENCIES:
            ecb[c] = tab["EUR"] / tab[c]
        extra = ecb.iloc[[-1]].copy()
        extra["Date"] = (tab.index.max() + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
        ecb = pd.concat([ecb, extra])
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr("eurofxref-hist.csv", ecb.to_csv(index=False))

        class Fake:
            def __enter__(self): return self
            def __exit__(self, *a): return False
            def raise_for_status(self): pass
            def iter_content(self, n): yield buf.getvalue()

        import requests
        seen = {}
        monkeypatch.setattr(requests, "get", lambda url, **kw: (seen.setdefault("url", url), Fake())[1])
        day = fx.update_from_ecb()
        assert seen["url"] == fx.ECB_URL and day == tab.index.max() + pd.Timedelta(days=1)
        assert fx.local_path().exists() and fx.latest()[0] == day          # yerel tablo artık kullanılıyor
        assert fx.stale_rates({"USD": fx.latest()[1]["USD"] * 0.8}) and not fx.stale_rates({"USD": fx.latest()[1]["USD"]})
    finally:
        fx.clear_cache()
