"""Yönetici paneli: streamlit run app.py"""
import hashlib
import io
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, "src")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import plotly.graph_objects as go  # noqa: E402
import streamlit as st  # noqa: E402

from radar import access, actions, anonymize, benchmark, ingest, mailer, pilot, pipeline, standards  # noqa: E402
from radar.reconcile import collection_events, reconcile, sender_key  # noqa: E402
from radar.store import Store, create_business, encrypt_backup, list_businesses  # noqa: E402

ROOT = Path(__file__).parent
SAMPLES = ROOT / "ornekler"
KEEP = ("sim", "ranked", "metrics", "opening", "gap_day", "simple_model", "n_train", "disputed_total", "obs", "as_of",
        "ctx", "outflows", "info")
MAPPABLE = {"invoices": ("Fatura dosyası", ingest.INVOICE_FIELDS, ingest.INVOICE_REQUIRED),
            "payments": ("Banka ekstresi", ingest.PAYMENT_FIELDS, ingest.PAYMENT_REQUIRED)}
STAGES = {"hatirlatma": "Hatırlatma", "mutabakat": "Mutabakat", "resmi": "Resmî bildirim"}

st.set_page_config(page_title="KOBİ Nakit Akışı Radarı", layout="wide")


def tl(x, compact: bool = False) -> str:
    """Türkçe para biçimi: 2.108.055 TL; compact=True ise 2,1 mn TL."""
    x = float(x)
    if compact and abs(x) >= 1e6:
        return f"{x / 1e6:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".") + " mn TL"
    return f"{x:,.0f}".replace(",", ".") + " TL"


def show_table(df, help: dict | None = None, **kwargs):
    """Tabloları Türkçe gösterir: tarih GG.AA.YYYY, "(TL)" sütunları binlik ayraçlı, olasılıklar yüzde."""
    config, df = {}, df.copy()
    for col in df.columns:
        tip = (help or {}).get(col)
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            config[col] = st.column_config.DateColumn(col, format="DD.MM.YYYY", help=tip)
        elif "(TL)" in col:
            df[col] = pd.to_numeric(df[col], errors="coerce").round(0)
            config[col] = st.column_config.NumberColumn(col, format="localized", help=tip)
        elif "olasılı" in col.lower() or "risk" in col.lower():
            df[col] = pd.to_numeric(df[col], errors="coerce").round(2)
            config[col] = st.column_config.NumberColumn(col, format="percent", help=tip)
        elif tip:
            config[col] = st.column_config.Column(col, help=tip)
    return st.dataframe(df, column_config=config, **kwargs)


def turkish_axes(fig):
    """Grafikte Türkçe sayı ayracı ve gün.ay biçimli tarih."""
    fig.update_layout(separators=",.", yaxis_tickformat=",.0f", xaxis_tickformat="%d.%m", xaxis_hoverformat="%d.%m.%Y",
                      yaxis_hoverformat=",.0f", legend=dict(orientation="h", y=-0.15))
    return fig
st.title("KOBİ Nakit Akışı Radarı")
st.caption("Mesajlar taslaktır; bu panel hiçbir mesajı kendiliğinden göndermez. "
           "Nasıl kullanılacağı: programla birlikte gelen KULLANIM_KILAVUZU.md dosyası.")


@st.cache_resource
def get_store(path: str) -> Store:
    return Store(path)


def secret_key(store: Store) -> str:
    return anonymize.business_key(anonymize.load_or_create_key(), store.business_id)


def _open(upload):
    buf = io.BytesIO(upload.getvalue())
    buf.name = upload.name
    return buf


def save_upload(store: Store, name: str, uploads, parse) -> None:
    """Dosya değiştiyse ayrıştırıp kaydeder; aynı dosya yeniden çizimde tekrar yazılmaz."""
    uploads = [u for u in (uploads if isinstance(uploads, list) else [uploads]) if u]
    if not uploads:
        return
    mapping = store.get(f"map_{name}", "{}") + (store.get("rates", "") + store.get("terms", "") if name == "invoices" else "")
    digest = hashlib.md5(b"".join(u.getvalue() for u in uploads) + mapping.encode()).hexdigest()
    if digest == store.get(f"hash_{name}"):
        return
    try:
        df, notes = parse(uploads)
    except ValueError as err:
        st.sidebar.error(str(err))
        tabular = [u for u in uploads if not u.name.lower().endswith(".xml")]
        if name in MAPPABLE and tabular:
            st.session_state[f"needmap_{name}"] = tabular[0]
        return
    st.session_state.pop(f"needmap_{name}", None)
    store.save(name, df)
    store.set(f"notes_{name}", json.dumps(notes, ensure_ascii=False))
    store.set(f"hash_{name}", digest)


def parse_invoices(uploads, terms, rates):
    frames, notes = [], []
    xml = [_open(u) for u in uploads if u.name.lower().endswith(".xml")]
    ledger_cheques, ledger_events = [], []
    for u in uploads:
        if not u.name.lower().endswith(".xml") and ingest.is_ledger(_open(u)):
            df, n, chq, ev = ingest.load_ledger(_open(u), terms, fallback_customer=Path(u.name).stem, with_events=True)
            frames.append(df)
            notes += n
            ledger_cheques.append(chq)
            ledger_events.append(ev)
        elif not u.name.lower().endswith(".xml"):
            df, n = ingest.load_invoices(_open(u), terms, json.loads(store.get("map_invoices", "{}")), rates)
            frames.append(df)
            notes += n
    if xml:
        df, n = ingest.load_ubl(xml, terms, rates)
        frames.append(df)
        notes += n
    frames = [f for f in frames if len(f)]
    if not frames:
        raise ValueError("Yüklenen dosyalardan okunabilen fatura çıkmadı.")
    found = [c for c in ledger_cheques if len(c)]
    if found and store.load("cheques") is None:
        store.save("cheques", pd.concat(found, ignore_index=True))
    # Cari hesaptaki tahsilat dağıtımları; satış dosyası cari ekstre değilse eski olaylar geçersizdir.
    store.save("ledger_events", pd.concat(ledger_events, ignore_index=True) if ledger_events
               else pd.DataFrame(columns=["date", "invoice_id", "amount"]))
    return pd.concat(frames, ignore_index=True).drop_duplicates("invoice_id"), notes


@st.cache_data(show_spinner="Demo şirketin 90 günlük kasası hesaplanıyor; 10-20 saniye sürer. Panel açık kaldıkça sonraki işlemler anında gelir...")
def run_demo(seed: int, include_projected: bool, today: str):
    res = pipeline.demo(seed=seed, as_of=today, include_projected=include_projected)
    return {k: res[k] for k in KEEP} | {"notes": [], "has_outflows": True, "unmatched": None, "last_activity": None}


@st.cache_data(show_spinner="Verileriniz işleniyor ve 90 günlük kasa hesaplanıyor; 10-20 saniye sürebilir. Veri değişmedikçe sonraki işlemler anında gelir...")
def run_own(path: str, rev: int, as_of: str, include_projected: bool):
    """`rev` kayıt her değiştiğinde artar; sonuç ancak o zaman yeniden hesaplanır. `path` işletmeyi ayırır."""
    store = get_store(path)
    notes = [n for name in ("invoices", "payments", "payables") for n in json.loads(store.get(f"notes_{name}", "[]"))]
    obs = store.apply_events(store.load("invoices"), as_of)
    obs = obs[obs["issue_date"] <= pd.Timestamp(as_of)]
    payments = store.load("payments")
    allocations, match_rate = None, None
    if payments is not None:
        payments = payments[payments["date"] <= pd.Timestamp(as_of)]
        obs, allocations, unmatched = reconcile(obs, payments, tol=float(store.get("match_tol", 0.01)),
                                                aliases=json.loads(store.get("sender_aliases", "{}")))
        incoming = float(payments["amount"].sum())
        match_rate = 1 - float(unmatched["amount"].sum()) / incoming if len(unmatched) and incoming else 1.0
        notes.append(f"Ekstre: {len(payments)} tahsilatın {len(payments) - len(unmatched)} tanesi faturalarla eşleşti "
                     f"(tutarın %{match_rate * 100:.0f}'i).")
        if len(unmatched):
            notes.append(f"Eşleşmeyen tahsilat tutarı: {tl(unmatched['amount'].sum())} "
                         "(müşterisi bulunamayan ya da fazla ödeme).")
    outflows, cheques, payables = store.load("outflows"), store.load("cheques"), store.load("payables")
    notes += json.loads(store.get("notes_cheques", "[]"))
    # Nakit takvimi için her çıkışın kaynağı ve kesinliği.
    if outflows is not None:
        outflows = outflows.assign(kaynak="Gider dosyası", tur="Planlı (dosyadan)")
    fixed = {k: float(store.get(f"fixed_{k}", 0)) for k in ("payroll", "muhtasar", "sgk", "kdv", "rent")}
    if any(fixed.values()):
        plan = ingest.fixed_cost_plan(as_of, payroll_day=int(float(store.get("fixed_payroll_day", 1))),
                                      rent_day=int(float(store.get("fixed_rent_day", 1))), **fixed)
        notes.append(f"Aylık sabit giderlerden {len(plan)} ödeme ({tl(plan['amount'].sum())}) eklendi.")
        plan = plan.assign(kaynak="Aylık sabit giderler", tur="Varsayım (elle girilen)")
        outflows = plan if outflows is None else pd.concat([outflows, plan], ignore_index=True)
    if payables is not None:
        flows, n = ingest.payables_to_outflows(payables, as_of)
        notes += n + [f"Ödenecek faturalar: {len(payables)} adet, {tl(payables['amount'].sum())}."]
        flows = flows.assign(kaynak="Ödenecek faturalar", tur="Kesin (borç faturası)")
        outflows = flows if outflows is None else pd.concat([outflows, flows], ignore_index=True)
    if cheques is not None:
        notes.append(f"Çek/senet portföyü: {len(cheques)} adet, {tl(cheques['amount'].sum())}.")
    # Pilot kayıtları biriktikçe bant iki uçta ayrı ayrı çevrimiçi ayarlanır (pilot.online_adjustment).
    # Tahsilat olayları: banka eşleştirmesi varsa onun dağıtımları, yoksa cari hesap ekstresindeki dağıtımlar.
    if allocations is None:
        ledger = store.load("ledger_events")
        allocations = ledger[ledger["date"] <= pd.Timestamp(as_of)] if ledger is not None and len(ledger) else None
    events = collection_events(obs, allocations)
    online = pilot.online_adjustment(store.pilot_records(), obs, events)

    def hook(calib):
        w0 = calib.get("widen", 1.0)
        w0 = (w0, w0) if np.isscalar(w0) else w0
        return calib | {"widen": (w0[0] * online["lo"], w0[1] * online["hi"]), "online": online}

    # Tahsilat kayıtları bugünden geride kalıyorsa tahmin, kayıtların son gününe göre kurulur.
    through = store.get("payments_through", "")
    through = (min(pd.Timestamp(through), pd.Timestamp(as_of)) if through
               else pipeline.payments_cutoff(obs.reset_index(drop=True), as_of))
    res = pipeline.forecast(obs.reset_index(drop=True), as_of, float(store.get("opening", 0)),
                            outflows if outflows is not None else pd.DataFrame({"date": [], "amount": []}),
                            include_projected=include_projected, cheques=cheques, calib_hook=hook,
                            payments_through=through, events=events)
    # Verideki son hareket: bundan sonraki ödemeler bilinmez, ödenmemiş görünür.
    dates = [obs["issue_date"].max(), obs["paid_date"].max()] + ([payments["date"].max()] if payments is not None else [])
    last = max(d for d in dates if pd.notna(d))
    # Giderler: gider dosyası ya da (dosya yoksa) elle girilen aylık sabit giderler; ikisi birbirinin yerine geçer.
    scope = {"banka_ekstresi": payments is not None,
             "giderler": store.load("outflows") is not None or any(fixed.values()),
             "odenecek_faturalar": payables is not None,
             "cekler": cheques is not None, "yeni_satislar": include_projected}
    return {k: res[k] for k in KEEP} | {"notes": notes, "has_outflows": outflows is not None,
                                        "unmatched": unmatched if payments is not None else None, "last_activity": last,
                                        "n_payments": len(payments) if payments is not None else None,
                                        "events": events, "match_rate": match_rate,
                                        "scope": scope, "cheques": cheques}


@st.cache_data(show_spinner="Açığı kapatacak tahsilat hesaplanıyor...")
def run_gap(key, _res):
    return pipeline.gap_summary(_res)


@st.cache_data(show_spinner=False)
def run_impact(key, _res, ids):
    return pipeline.invoice_impact(_res, ids)


@st.cache_data(show_spinner=False)
def run_fx_shift(key, _res, pct):
    return pipeline.fx_shift(_res, pct)


@st.cache_data(show_spinner=False)
def run_customer_delay(key, _res, customers, days):
    return pipeline.customer_delay(_res, customers, days)


SCOPE_NAMES = {'banka_ekstresi': 'banka ekstresi', 'giderler': 'giderler (gider dosyası ya da aylık sabit giderler)', 'odenecek_faturalar': 'ödenecek faturalar', 'cekler': 'çek/senet portföyü', 'yeni_satislar': 'yeni satışlar'}


@st.cache_data(show_spinner=False)
def run_scenario(key, _res, collect_ids, delay_labels, delay_days):
    return pipeline.scenario(_res, collect_ids, delay_labels=delay_labels, delay_days=delay_days)


@st.cache_data(show_spinner="Geçmiş tarihlere dönülüp tahmin yeniden üretiliyor; yarım dakikayı bulabilir...")
def run_backtest(obs, as_of):
    return pipeline.backtest_own(obs, as_of)


@st.cache_data(show_spinner="Pilot raporu hazırlanıyor; geçmiş tarihlerde test de yapıldığı için yarım dakika kadar sürer...")
def run_pilot(key, _res, label, hide):
    secret = secret_key(store) if hide else None
    r = pilot.build(_res["obs"], _res["as_of"], res=_res, label=label, key=secret,
                    unmatched=_res.get("unmatched"), n_payments=_res.get("n_payments"))
    return pilot.render(r).encode("utf-8")


def anonymous_package(store: Store, seller: str):
    extra = {"giderler": store.load("outflows"), "odenecekler": store.load("payables"), "cekler": store.load("cheques")}
    return anonymize.package(seller or "İşletme", store.load("invoices"), secret_key(store),
                             store.load("payments"), extra, records=store.pilot_records())


BUSINESSES = list_businesses()
# Seçili işletme, seçim kutusundan ayrı tutulur: kutu demo modunda çizilmediğinde seçim kaybolmasın.
if st.session_state.get("active_business") not in BUSINESSES:
    st.session_state["active_business"] = next(iter(BUSINESSES))
store = get_store(str(BUSINESSES[st.session_state["active_business"]]))

# İsteğe bağlı panel parolası (ortak kullanılan bilgisayarlar için; KVKK rehberi: kullanıcı hesap yönetimi).
if access.enabled() and not st.session_state.get("auth_ok"):
    st.title("KOBİ Nakit Akışı Radarı")
    attempt = st.text_input("Panel parolası", type="password", key="login_pw")
    if st.button("Giriş"):
        if access.check(attempt):
            st.session_state["auth_ok"] = True
            store.audit("panel girişi")
            st.rerun()
        else:
            store.audit("başarısız panel girişi")
            st.error("Parola yanlış.")
    st.stop()


SAMPLE_NAME = "Örnek İşletme (uydurma veri)"


def add_sample_business():
    """Tanıtım için bugünün tarihine göre üretilmiş uydurma bir işletme; varsa verisi yenilenir."""
    import tempfile

    from radar import synthetic
    today = f"{pd.Timestamp.now():%Y-%m-%d}"
    path = list_businesses().get(SAMPLE_NAME) or create_business(SAMPLE_NAME)
    sample = get_store(str(path))
    with tempfile.TemporaryDirectory() as tmp:
        folder = Path(tmp)
        synthetic.export_samples(folder, seed=7, as_of=today)
        sample.save("invoices", ingest.load_invoices(folder / "faturalar.csv")[0])
        sample.save("payments", ingest.load_payments(folder / "ekstre.csv")[0])
        sample.save("outflows", ingest.load_schedule(folder / "giderler.csv"))
        sample.save("payables", ingest.load_payables(folder / "odenecekler.csv")[0])
        sample.save("cheques", ingest.load_cheques(folder / "cekler.csv")[0])
    obs = synthetic.observe(synthetic.generate(seed=7, as_of=today), today)
    # Açılış kasası bilerek düşük: tanıtımda risk ve "açığı kapatmak için ne gerekir" bölümü görünsün.
    sample.set("opening", round(synthetic.cash_plan(obs, today, opening_months=0.3)[0], -3))
    sample.set("seller", "Örnek Ticaret A.Ş. (MERSİS 0000000000000000)")
    st.session_state["active_business"] = SAMPLE_NAME


def add_business():
    try:
        create_business(st.session_state.get("new_business", ""))
        st.session_state["active_business"] = " ".join(st.session_state["new_business"].split())
        st.session_state["new_business"] = ""
    except ValueError as err:
        st.session_state["business_error"] = str(err)
with st.sidebar:
    source = st.radio("Veri", ["Demo şirket", "Kendi verim"])
    include_projected = st.toggle("Gelecek satışları hesaba kat", True,
                                  help="Önümüzdeki 90 günde kesilecek faturaları son 90 günün satış hızına göre tahmine "
                                       "katar. Kapatırsanız yalnızca bugün açık olan faturalar sayılır.")
    if source == "Demo şirket":
        seed = st.number_input("Demo şirket no", 1, 99, 7, help="Farklı bir uydurma şirket görmek için değiştirin.")
        seller = st.text_input("Mesajlardaki imza (ticaret unvanı ve MERSİS no)", "Örnek Ticaret A.Ş. (MERSİS 0000000000000000)")
    else:
        names = list(BUSINESSES)
        chosen = st.selectbox("İşletme", names, index=names.index(st.session_state["active_business"]),
                              help="Mali müşavirler birden çok işletmeyi ayrı ayrı izleyebilir. Her işletmenin "
                                   "dosyaları, ayarları ve kayıtları ayrı saklanır.")
        if chosen != st.session_state["active_business"]:
            st.session_state["active_business"] = chosen
            st.rerun()
        with st.expander("İşletme ekle"):
            st.text_input("Yeni işletmenin adı", key="new_business")
            st.button("Ekle", on_click=add_business)
            st.button("Tanıtım için örnek işletme ekle", on_click=add_sample_business,
                      help="Bugünün tarihine göre üretilmiş uydurma faturalar, banka ekstresi, giderler, borçlar ve "
                           "çeklerle dolu bir işletme açar. Gerçek bir işletmeye ait değildir.")
            if st.session_state.get("business_error"):
                st.error(st.session_state.pop("business_error"))
        has_data = store.load("invoices") is not None
        with st.expander("1. Temel bilgiler", expanded=True):
            as_of = st.date_input("Tahmin tarihi", format="DD.MM.YYYY",
                                  help="Genellikle bugün. Geçmiş bir tarih seçerseniz o güne kadarki veriyle tahmin yapılır.")
            opening = st.number_input("Kasa ve bankadaki toplam para (TL)", 0.0, value=float(store.get("opening", 0)),
                                      step=10_000.0, help="Her kullanımda güncelleyin; tahmin bu tutardan başlar.")
            saved_through = store.get("payments_through", "")
            through = st.date_input("Tahsilatlar hangi tarihe kadar işlendi? (isteğe bağlı)", format="DD.MM.YYYY",
                                    value=pd.Timestamp(saved_through).date() if saved_through else None,
                                    help="Yüklediğiniz dosyada tahsilatlar bugüne kadar işlenmemişse (ör. muhasebe programından "
                                         "birkaç gün önce alındıysa ya da kayıtlar yasal süre içinde ama günü gününe işlenmiyorsa) "
                                         "son işlenen günü girin. "
                                         "Boş bırakılırsa kayıtlardan tahmin edilir. O günden sonra gelmiş olabilecek "
                                         "ödemeler kasa bakiyenizin içinde sayılır, ikinci kez tahsilat olarak eklenmez.")
            store.set("payments_through", f"{pd.Timestamp(through):%Y-%m-%d}" if through else "")
            # TCMB tablosu yalnızca kullanım izni olan pakette bulunur (bkz. benchmark.py); yoksa alan gösterilmez.
            if benchmark.available():
                sector_options = [("", "Seçilmedi")] + benchmark.sectors()
                codes = [c for c, _ in sector_options]
                saved_sector = store.get("sector", "")
                sector = st.selectbox("Sektör (karşılaştırma için, isteğe bağlı)", codes,
                                      index=codes.index(saved_sector) if saved_sector in codes else 0,
                                      format_func=dict(sector_options).get,
                                      help="Tahsil sürenizi Türkiye'de aynı sektör ve ölçekteki firmalarla karşılaştırmak için "
                                           f"({benchmark.SOURCE}). Tahmini etkilemez.")
                sizes = list(benchmark.SIZES)
                size = st.selectbox("Ölçek", sizes, index=sizes.index(store.get("size", "kucuk")) if store.get("size", "kucuk") in sizes else 1,
                                    format_func=benchmark.SIZES.get, help="TÜİK/TCMB ölçek sınıfı (çalışan sayısı ve ciroya göre).")
                store.set("sector", sector)
                store.set("size", size)
        with st.expander("2. Dosyalar", expanded=not has_data):
            st.caption("Yüklediğiniz dosya, aynı türdeki eski dosyanın yerine geçer. Her şey yalnızca bu bilgisayarda saklanır.")
            invoice_upload = st.file_uploader("Satışlar: fatura listesi, cari hesap ekstresi ya da e-Fatura XML (zorunlu)",
                                              ["csv", "xlsx", "xls", "xml"], accept_multiple_files=True)
            uploads = {name: st.file_uploader(label, ["csv", "xlsx", "xls"]) for name, label in (
                ("payments", "Banka ekstresi"), ("outflows", "Planlı giderler"),
                ("payables", "Ödenecek faturalar"), ("cheques", "Çek / senet portföyü"))}
        with st.expander("3. Aylık sabit giderler (gider dosyanız yoksa)"):
            st.caption("Vergi takvimine göre yerleştirilir: muhtasar ayın 26'sı, KDV 28'i, SGK primi ay sonu; "
                       "hafta sonuna denk gelen son gün ilk iş gününe kayar. Yüklenen gider dosyasına eklenir.")
            fixed = {k: st.number_input(lbl, 0.0, value=float(store.get(f"fixed_{k}", 0)), step=1000.0, key=f"fx_{k}")
                     for k, lbl in (("payroll", "Net maaşlar (TL/ay)"), ("muhtasar", "Muhtasar (TL/ay)"),
                                    ("sgk", "SGK primi (TL/ay)"), ("kdv", "KDV (TL/ay, tahmini)"), ("rent", "Kira (TL/ay)"))}
            fixed["payroll_day"] = st.number_input("Maaş günü", 1, 31, int(store.get("fixed_payroll_day", 1)))
            fixed["rent_day"] = st.number_input("Kira günü", 1, 31, int(store.get("fixed_rent_day", 1)))
        with st.expander("4. Mesaj ayarları"):
            seller = st.text_input("İmza: ticaret unvanı ve MERSİS no", store.get("seller", ""),
                                   placeholder="Örnek Ticaret A.Ş. (MERSİS 0123456789000015)",
                                   help="Ticari İletişim ve Ticari Elektronik İletiler Hakkında Yönetmelik m.8: tacirler "
                                        "ticaret unvanı ve MERSİS numarasını, esnaflar ad soyad ile T.C. kimlik ya da "
                                        "vergi kimlik numarasını yazmalıdır.")
            iban = st.text_input("Tahsilat IBAN'ı", store.get("iban", ""), placeholder="TR00 0000 0000 0000 0000 0000 00",
                                 help="Girerseniz taslaklara 'açıklamaya fatura numarasını yazın' talimatıyla eklenir.")
            bank = st.text_input("Banka adı", store.get("bank", ""))
            st.caption("E-posta ile göndermek için (isteğe bağlı). Parola kaydedilmez. Gmail ve Outlook'ta hesap "
                       "parolası yerine uygulama parolası gerekir.")
            mail = mailer.MailConfig(
                host=st.text_input("SMTP sunucusu", store.get("smtp_host", ""), placeholder="smtp.gmail.com"),
                port=int(st.number_input("Port", 1, 65535, int(store.get("smtp_port", 587)))),
                username=st.text_input("Kullanıcı adı (e-posta adresiniz)", store.get("smtp_user", "")),
                password=st.text_input("Parola", type="password"))
        with st.expander("5. Pilot: takma adlı veri paketi"):
            st.write("Yüklediğiniz dosyaların, müşteri adları ve vergi numaraları takma adlarla değiştirilmiş bir "
                     "kopyası. Tutar ve tarihler aynen kalır; e-posta ve telefon silinir; banka açıklamaları tümüyle "
                     "yeniden yazılır. Pilot çalışması için paylaşılacak dosya budur.")
            if has_data and st.button("Takma adlı paketi hazırla"):
                blob, summary = anonymous_package(store, seller)
                store.audit("takma adlı paket hazırlandı", f"{summary['fatura']} fatura, {summary['müşteri']} müşteri")
                st.download_button("Paketi indir (zip)", blob, f"{summary['işletme_takma_adı']}.zip", "application/zip")
                st.caption(f"{summary['fatura']} fatura, {summary['müşteri']} müşteri, dönem {summary['dönem']}. "
                           "Göndermeden önce zip dosyasını açıp gözle kontrol edin.")
            st.caption(f"Takma adları üreten gizli anahtar yalnızca bu bilgisayarda: {anonymize.key_path()}. "
                       "Anahtar paylaşılmaz; aynı anahtar her ay aynı takma adları verir.")
            pilot_on = st.checkbox("Pilota katılıyorum: her hafta ileriye dönük kaydı kendiliğinden al",
                                   store.get("pilot_on", "0") == "1",
                                   help="Panel haftada bir, bugünün tahmininden önümüzdeki 14 ve 30 günün tahsilat "
                                        "tahminini kaydeder. Kayıtlar değiştirilemez; süre dolunca gerçekleşenle "
                                        "karşılaştırılır ve takma adlı pakete eklenir.")
            store.set("pilot_on", int(pilot_on))
        with st.expander("Diğer ayarlar"):
            match_tol = st.number_input(
                "Banka eşleştirme toleransı (TL)", 0.0, 1000.0, float(store.get("match_tol", 0.01)), step=1.0,
                help="Gelen para ile fatura tutarı arasında kabul edilen fark (ör. havale masrafı). Yükseltirseniz "
                     "daha çok eşleşme olur, ama yanlış eşleşme riski de artar.")
            store.set("match_tol", match_tol)
            terms = st.number_input("Vadesi yazmayan faturalar için vade (gün)", 0, 365, int(store.get("terms", 30)),
                                    help="TTK m.1530: vade yazmıyorsa borçlu, faturayı aldıktan 30 gün sonra temerrüde düşer.")
            rates_text = st.text_input("Döviz kurları (dövizli fatura varsa)", store.get("rates", ""),
                                       placeholder="USD=41,50; EUR=48,20",
                                       help="Dövizli faturalar bu kurla TL'ye çevrilir. Kur girilmeyen döviz tahmine katılmaz.")
            st.caption(f"Verilerin saklandığı dosya: {store.path}")
            undoable = [n for n in ("invoices", "payments", "outflows", "payables", "cheques") if store.can_undo(n)]
            if undoable:
                names = {"invoices": "Satışlar", "payments": "Banka ekstresi", "outflows": "Planlı giderler",
                         "payables": "Ödenecek faturalar", "cheques": "Çek / senet"}
                which = st.selectbox("Son yüklemeyi geri al", undoable, format_func=names.get)
                if st.button("Önceki dosyaya dön"):
                    store.undo(which)
                    if which == "invoices" and store.can_undo("ledger_events"):
                        store.undo("ledger_events")             # olaylar satış dosyasıyla birlikte geri alınır
                    store.set(f"hash_{which}", "")
                    st.rerun()
            st.write("**Şifreli yedek.** Yüklenen tablolar, ayarlar, mesaj ve pilot kayıtları tek dosyada, parolayla "
                     "şifreli (AES-256). Parolayı unutursanız yedek açılamaz.")
            backup_pw = st.text_input("Yedek parolası (en az 8 karakter)", type="password", key="backup_pw")
            if len(backup_pw) >= 8:
                st.download_button("Şifreli yedeği indir", encrypt_backup(store.backup_bytes(), backup_pw),
                                   f"kobi_radar_yedek_{pd.Timestamp.now():%Y%m%d}.kryedek",
                                   on_click=lambda: store.audit("şifreli yedek indirildi"))
            restore_file = st.file_uploader("Yedekten geri yükle", ["kryedek", "db"], key="restore_file")
            if restore_file is not None:
                restore_pw = st.text_input("Yedeğin parolası", type="password", key="restore_pw")
                if st.checkbox("Mevcut verinin yerine yedeği yükle", key="restore_sure") and st.button("Geri yükle"):
                    try:
                        safety = store.restore(restore_file.getvalue(), restore_pw or None)
                        st.success(f"Yedek yüklendi. Önceki veri şu dosyada saklandı: {safety}")
                    except ValueError as err:
                        st.error(str(err))
            st.write("**Kayıtlı veriyi sil.** Yüklenen tablolar silinir; itiraz, ödeme sözü ve mesaj kayıtları korunur.")
            sure = st.checkbox("Eminim")
            if st.button("Tabloları sil", disabled=not sure):
                store.clear()
                for name in ("invoices", "payments", "outflows", "cheques", "payables"):
                    store.set(f"hash_{name}", "")
                st.rerun()
            st.write("**İşletmeyi tamamen sil (imha).** Bu işletmenin bütün verisi, kayıtları, pilot kayıtları ve "
                     "geri yükleme öncesi kopyaları bilgisayardan kalıcı olarak silinir. Geri alınamaz; önce şifreli "
                     "yedek almayı düşünün.")
            confirm = st.text_input("Onay için işletmenin adını yazın", key="destroy_confirm")
            if st.button("Tamamen sil", disabled=confirm.strip() != st.session_state["active_business"]):
                gone = store.destroy()
                get_store.clear()
                st.session_state.pop("active_business", None)
                st.success(f"{len(gone)} dosya silindi.")
                st.rerun()
            st.write("**Panel parolası** (isteğe bağlı; ortak kullanılan bilgisayarlar için).")
            if access.enabled():
                old = st.text_input("Mevcut parola", type="password", key="pw_old")
                if st.button("Parolayı kaldır"):
                    try:
                        access.remove(old)
                        store.audit("panel parolası kaldırıldı")
                        st.rerun()
                    except ValueError as err:
                        st.error(str(err))
            else:
                new = st.text_input(f"Yeni parola (en az {access.MIN_LENGTH} karakter)", type="password", key="pw_new")
                if st.button("Parolayı ayarla"):
                    try:
                        access.set_password(new)
                        st.session_state["auth_ok"] = True
                        store.audit("panel parolası ayarlandı")
                        st.rerun()
                    except ValueError as err:
                        st.error(str(err))
            st.caption("İşlem kayıtları: yükleme, paket, yedek, geri yükleme, silme ve giriş denemeleri "
                       "'Tahmin doğruluğu' sekmesinin altında görünür.")

        if float(store.get("opening", 0)) != float(opening):
            store.set("opening_date", f"{pd.Timestamp.now():%Y-%m-%d}")     # kapanış kasası ölçümü için
        for key, value in (("opening", opening), ("terms", int(terms)), ("seller", seller), ("rates", rates_text),
                           ("iban", iban), ("bank", bank), ("smtp_host", mail.host), ("smtp_port", mail.port),
                           ("smtp_user", mail.username)):
            store.set(key, value)
        for k, v in fixed.items():
            store.set(f"fixed_{k}", v)
        save_upload(store, "invoices", invoice_upload,
                    lambda ups: parse_invoices(ups, int(terms), ingest.parse_rates(rates_text)))
        save_upload(store, "payments", uploads["payments"],
                    lambda ups: ingest.load_payments(_open(ups[0]), json.loads(store.get("map_payments", "{}"))))
        save_upload(store, "outflows", uploads["outflows"], lambda ups: (ingest.load_schedule(_open(ups[0])), []))
        save_upload(store, "payables", uploads["payables"], lambda ups: ingest.load_payables(_open(ups[0]), int(terms)))
        save_upload(store, "cheques", uploads["cheques"], lambda ups: ingest.load_cheques(_open(ups[0])))

own = source == "Kendi verim"
for name, (title, fields, required) in MAPPABLE.items():
    upload = st.session_state.get(f"needmap_{name}") if own else None
    if upload is None:
        continue
    st.subheader(f"{title}: sütunları eşleştirin")
    st.write("Dosyadaki başlıklar otomatik tanınamadı. Her alan için dosyanızdaki karşılığını seçin; "
             "seçiminiz kaydedilir ve aynı biçimdeki sonraki dosyalarda yeniden sorulmaz.")
    headers = ingest.columns(_open(upload))
    saved = json.loads(store.get(f"map_{name}", "{}"))
    with st.form(f"map_{name}"):
        chosen = {}
        for col, field in zip(st.columns(4) * 2, fields):
            label = ingest.FIELD_LABELS[field] + (" *" if field in required else "")
            options = ["(yok)"] + headers
            pick = col.selectbox(label, options, index=options.index(saved[field]) if saved.get(field) in headers else 0)
            if pick != "(yok)":
                chosen[field] = pick
        if st.form_submit_button("Eşleştirmeyi kaydet"):
            missing = [ingest.FIELD_LABELS[f] for f in required if f not in chosen]
            if missing:
                st.error("Zorunlu alanlar seçilmedi: " + ", ".join(missing))
            else:
                store.set(f"map_{name}", json.dumps(chosen, ensure_ascii=False))
                st.rerun()
    st.stop()

if not own:
    today = f"{pd.Timestamp.now():%Y-%m-%d}"            # demo şirket her gün bugüne göre üretilir
    res = run_demo(int(seed), include_projected, today)
    res_key = ("demo", int(seed), include_projected, today)
elif store.load("invoices") is None:
    st.info("Başlamak için soldan fatura listenizi (CSV / Excel) ya da e-fatura XML dosyalarınızı yükleyin. "
            "Fatura listesinde en az şu sütunlar olmalı: Fatura No, Cari Unvan, Fatura Tarihi, Tutar. "
            "Vade Tarihi, VKN, Ödeme Tarihi ve Kalan sütunları varsa kullanılır. Muhasebe programınızın cari hesap "
            "ekstresi ya da muavin defteri (Borç / Alacak sütunlarıyla) de doğrudan yüklenebilir.")
    if SAMPLES.exists():
        st.write("Biçimi görmek için örnek dosyalar:")
        for col, name in zip(st.columns(6), ["faturalar.csv", "ekstre.csv", "cari_ekstre.csv", "giderler.csv",
                                             "odenecekler.csv", "cekler.csv"]):
            col.download_button(name, (SAMPLES / name).read_bytes(), name)
        st.caption((SAMPLES / "OKU.txt").read_text(encoding="utf-8"))
    st.write("Önce denemek isterseniz, bugünün tarihine göre uydurma verilerle dolu bir örnek işletme açabilirsiniz:")
    st.button("Tanıtım için örnek işletme ekle", on_click=add_sample_business, key="sample_main")
    st.stop()
else:
    res = run_own(str(store.path), store.rev, str(as_of), include_projected)
    res_key = ("own", str(store.path), store.rev, str(as_of), include_projected)

sim, m = res["sim"], res["metrics"]


def record(invoice_id, kind, value=""):
    """Olayı panelde seçili tarihe yazar; bugünse saatiyle birlikte."""
    day = pd.Timestamp(as_of)
    now = pd.Timestamp.now()
    store.add_event(invoice_id, kind, value, now if day.date() == now.date() else day + pd.Timedelta(hours=12))
    st.rerun()


stale = res.get("last_activity")
if stale is not None and (pd.Timestamp(res["as_of"]) - stale).days > 7:
    st.error(f"Verinizdeki en son hareket {stale:%d.%m.%Y} tarihli, tahmin tarihinden "
             f"{(pd.Timestamp(res['as_of']) - stale).days} gün önce. Bu arada gelen ödemeler bilinmediği için ödenmemiş "
             f"sayılıyor; vadesi geçmiş alacak ve risk olduğundan yüksek görünür. Güncel dosyaları yükleyin ya da "
             f"tahmin tarihini {stale:%d.%m.%Y} yapın.")
lag_days = res["info"].get("payments_lag", 0)
if lag_days:
    st.warning(f"Tahsilat kayıtları {res['info']['payments_through']:%d.%m.%Y} tarihinde bitiyor ({lag_days} gün önce). "
               "O günden sonra gelmiş olabilecek ödemeler, girdiğiniz kasa bakiyesinin içinde sayıldı; açık görünen "
               "faturaların bir kısmı aslında ödenmiş olabilir. Kasa bakiyesini bugünkü banka bakiyesiyle girin. "
               "Tarih yanlışsa sol menüden \"Tahsilatlar hangi tarihe kadar işlendi?\" alanını düzeltin.")
if own and store.get("pilot_on", "0") == "1" and pilot.record_due(store.pilot_records(), res["as_of"],
                                                                  res.get("last_activity")) is None:
    with st.spinner("Bu haftanın pilot kaydı alınıyor; yarım dakika kadar sürer..."):
        weekly = pd.concat([pilot.forward_record(res["obs"], res["as_of"]), pilot.cash_record(res)], ignore_index=True)
    digest = hashlib.sha256("|".join(store.get(f"hash_{n}", "") for n in
                                     ("invoices", "payments", "outflows", "payables", "cheques")).encode()).hexdigest()
    meta = {"surum": pilot.VERSION, "kesim": f"{pd.Timestamp(res['as_of']):%Y-%m-%d}",
            "son_hareket": f"{res['last_activity']:%Y-%m-%d}", "veri_ozeti": digest[:16],
            "yontem": "müşteri medyanı (basit)" if res["simple_model"] else "LightGBM + müşteri medyanı birleşimi",
            "eslesme_orani": res.get("match_rate"), "kapsam": res.get("scope", {}),
            "acilis_guncel": store.get("opening_date") == f"{pd.Timestamp(res['as_of']):%Y-%m-%d}",
            "cevrimici_ayar": res["ctx"]["calib"].get("online"), "genisletme": res["info"].get("widen")}
    if store.add_pilot_record(res["as_of"], weekly, opening=res["opening"], meta=meta):
        st.toast("Bu haftanın pilot kaydı alındı.")
    if res.get("match_rate") is not None and res["match_rate"] < pilot.MIN_MATCH_RATE:
        st.warning(f"Banka tahsilatlarının yalnızca %{res['match_rate'] * 100:.0f}'i faturalarla eşleşti. Bu haftanın "
                   "pilot kaydı uyarılı sayılır ve doğruluk ölçümüne girmez; eşleşmeyenleri 'Tahsilat işleri' "
                   "sekmesinden müşterilere bağlayın.")
if m["delay_trend_days"] >= 3:
    st.warning(f"Müşterilerinizin ödemeleri son 90 günde, önceki 90 güne göre medyan {m['delay_trend_days']:.0f} gün "
               "daha geç geliyor. Gecikmeler uzamaya devam ederse tahmin iyimser kalabilir; kötümser çizgiyi esas alın.")
if res["simple_model"]:
    st.info(f"Vadesi dolmuş {res['n_train']} fatura bulundu. Bu kadar veriyle öğrenen model yerine "
            "müşteri alışkanlığına dayalı basit tahmin kullanılıyor; bant daha geniş ve daha az kişisel olur.")
if not res["has_outflows"]:
    st.warning("Gider planı yüklenmedi: grafik yalnızca tahsilatları gösteriyor, kasa açığı hesaplanamaz.")

c = st.columns(5)
c[0].metric("Kasa ve banka", tl(res["opening"], compact=True), help="Bugün kasada ve bankada olan toplam para.")
c[1].metric("Açık alacak", tl(m["open_ar"], compact=True), help="Müşterilerin henüz ödemediği faturaların toplamı.")
c[2].metric("Vadesi geçmiş", tl(m["overdue_ar"], compact=True), help="Açık alacağın vadesi dolmuş kısmı.")
c[3].metric("Ortalama tahsil süresi", f"{m['dso']:.0f} gün",
            help="Alacaklarınız ortalama kaç günlük satışa denk geliyor (DSO). Düşük olması iyidir.")
c[4].metric("Eksiye düşme riski", f"%{sim.prob_any_breach * 100:.0f}",
            help="Önümüzdeki 90 gün içinde kasanın en az bir gün eksiye düşme olasılığı. Bağımsız doğrulamada bu "
                 "olasılıklar ortaya doğru sıkışık çıktı (Spiegelhalter testi): yüksek riskte gerçek risk gösterilenden "
                 "yüksek, düşük riskte düşük. Karar için kötümser çizgiyi esas alın.")
if own and store.get("sector"):
    line = benchmark.compare(m["dso"], store.get("sector"), store.get("size", "kucuk"))
    if line:
        st.info(line + " Tanımlar yakın ama aynı değil: TCMB oranı yıllık ortalama alacağa, buradaki süre bugünkü "
                "açık alacağa dayanır.")
if sim.prob_any_breach >= 0.5:
    st.error(f"Eksiye düşme riski yüksek (%{sim.prob_any_breach * 100:.0f}). Bağımsız doğrulamada %80 gösterilen "
             "durumlarda gerçekleşme %92 oldu: yüksek riskte gerçek risk gösterilenden daha yüksek olabilir. "
             "Ödeme ve tahsilat kararlarını kötümser senaryoya göre verin.")

if sim.breach_day is not None:
    st.warning(f"Kötümser senaryoda kasa {sim.breach_day}. günde ({sim.dates[sim.breach_day]:%d.%m.%Y}) eksiye düşüyor. "
               "Ne yapılabileceği aşağıda, \"Kasa tahmini\" sekmesindeki \"Açığı kapatmak için ne gerekir?\" bölümünde.")
elif res["has_outflows"]:
    st.success("Kötümser senaryoda bile kasa 90 gün boyunca artıda kalıyor.")

notes = list(res["notes"])
if res["disputed_total"]:
    notes.append(f"İtirazlı {tl(res['disputed_total'])} alacak tahmine ve hatırlatma listesine dahil edilmedi.")
if m["over_60_terms"]:
    notes.append(f"{m['over_60_terms']} açık faturada vade 60 günden uzun. TTK m.1530'a göre alacaklı KOBİ ise ya da "
                 "borçlu büyük işletmeyse vade 60 günü aşamaz; bu sözleşmeleri gözden geçirin.")
if notes:
    with st.expander(f"Veri notları ({len(notes)})"):
        for note in notes:
            st.write("• " + note)

scope = res.get("scope")
if own and scope:
    info = res["info"]
    missing = [SCOPE_NAMES[k] for k, v in scope.items() if not v]
    age = (pd.Timestamp(res["as_of"]) - res["last_activity"]).days if res.get("last_activity") is not None else None
    with st.expander("Veri kalitesi ve kapsam" + (" — eksik kaynak var" if missing else "")):
        q = st.columns(4)
        q[0].metric("Son hareket", f"{age} gün önce" if age is not None else "–",
                    help="Verideki en son fatura ya da ödeme. Bir haftadan eskiyse gelen ödemeler bilinmez.")
        q[1].metric("Banka eşleşmesi", f"%{res['match_rate'] * 100:.0f}" if res.get("match_rate") is not None else "ekstre yok",
                    help="Gelen paranın faturalara bağlanabilen kısmı. %80'in altında tahminler ve pilot ölçümü güvenilmez.")
        q[2].metric("Geçmiş", f"{(res['obs']['issue_date'].max() - info['history_from']).days / 30.4:.0f} ay",
                    help="12 aydan kısa geçmişte tahmin, işletmenin kendi geçmişiyle sınanamaz.")
        q[3].metric("Yöntem", "Basit (medyan)" if res["simple_model"] else "Birleşik model",
                    help="Birleşik model: LightGBM ile müşterinin geçmiş gecikme medyanının ortalaması. Vadesi dolmuş "
                         "fatura 300'den azsa yalnızca müşteri medyanı kullanılır.")
        if missing:
            st.write("**Kapsam dışı:** " + ", ".join(missing) + ". Bunlar kasa tahminine dahil değil; kasa grafiği "
                     "yalnızca girilen kaynakları gösterir.")
        else:
            st.write("Bütün kaynaklar dahil: banka ekstresi, giderler, ödenecek faturalar, çekler, yeni satışlar.")

tab_cash, tab_collect, tab_accuracy = st.tabs(["Kasa tahmini", "Tahsilat işleri", "Tahmin doğruluğu"])

with tab_cash:
    fig = go.Figure()
    fig.add_scatter(x=sim.dates, y=sim.p90, line=dict(width=0), showlegend=False, hoverinfo="skip")
    fig.add_scatter(x=sim.dates, y=sim.p10, fill="tonexty", line=dict(width=0), name="Olası aralık (%80)",
                    fillcolor="rgba(31,119,180,0.2)")
    fig.add_scatter(x=sim.dates, y=sim.p50, name="Orta tahmin (P50)", line=dict(color="rgb(31,119,180)"))
    fig.add_hline(y=0, line_dash="dash", line_color="crimson")
    fig.update_layout(height=380, margin=dict(l=0, r=0, t=10, b=0), yaxis_title="Kasa (TL)", hovermode="x unified")
    turkish_axes(fig)
    st.plotly_chart(fig, width="stretch")
    st.caption("Mavi bant: kasanızın %80 olasılıkla içinde kalacağı aralık. Bandın alt kenarı kötümser, üst kenarı "
               "iyimser durumdur. Çizgi orta tahmin (P50, medyan): gerçekleşenin altında ya da üstünde kalma olasılığı "
               "eşittir. Kırmızı kesikli çizgi sıfır.")
    if scope and not all(scope.values()):
        st.caption("Kapsam dışı (grafiğe dahil değil): "
                   + ", ".join(SCOPE_NAMES[k] for k, v in scope.items() if not v) + ".")
    with st.expander("13 haftalık plan"):
        st.caption("Bilinen çıkışlar (giderler, borçlar) kesin kabul edilir. Tahsilat sütunları tahmindir: açık faturalar "
                   "müşterilerin geçmiş ödeme davranışından, yeni satışlar son 90 günün satış hızından gelir.")
        show_table(pipeline.weekly_table(res), width="stretch", hide_index=True,
                   help={"Eksiye düşme olasılığı": "O hafta içinde kasanın en az bir gün eksiye düşme olasılığı."})
    with st.expander("Nakit takvimi: her kalem ve ne kadar kesin olduğu"):
        flows = res["outflows"].copy()
        items = pd.DataFrame({
            "Tarih": pd.to_datetime(flows["date"]), "Kalem": flows["label"] if "label" in flows else "",
            "Kaynak": flows["kaynak"] if "kaynak" in flows else "Planlı giderler",
            "Tür": flows["tur"] if "tur" in flows else "Planlı", "Tutar (TL)": -flows["amount"].astype(float)})
        chq = res.get("cheques")
        if chq is not None and len(chq):
            items = pd.concat([items, pd.DataFrame({
                "Tarih": pd.to_datetime(chq["date"]), "Kalem": "Çek/senet tahsilatı", "Kaynak": "Çek portföyü",
                "Tür": "Olasılıklı (karşılıksız çıkma riski)", "Tutar (TL)": chq["amount"].astype(float)})])
        horizon_end = sim.dates[-1]
        items = items[(items["Tarih"] > pd.Timestamp(res["as_of"])) & (items["Tarih"] <= horizon_end)]
        st.caption("Eksi tutar çıkış, artı tutar giriştir. Açık faturalardan ve yeni satışlardan gelecek tahsilat tek tek "
                   "kalem değil, olasılıklı tahmindir; haftalık toplamları '13 haftalık plan' tablosundadır.")
        show_table(items.sort_values("Tarih"), width="stretch", hide_index=True)

    st.subheader("Açığı kapatmak için ne gerekir?")
    gap = run_gap(res_key, res)
    if gap["gap"] == 0:
        st.write("Kötümser senaryoda kasa açığı görünmüyor.")
    else:
        day = sim.dates[gap["gap_day"]]
        text = f"Kötümser senaryoda en derin açık **{tl(gap['gap'])}** ({day:%d.%m.%Y}). "
        if gap["k"]:
            which = "ilk faturası" if gap["k"] == 1 else f"ilk {gap['k']} faturası"
            text += (f"Aşağıdaki listenin **{which}** ({tl(gap['amount'])}) bir hafta içinde "
                     "tahsil edilirse kötümser senaryoda da kasa artıda kalır.")
        else:
            text += (f"Listedeki öncelikli faturaların tamamı ({tl(gap['amount'])}) tahsil edilse de açık kapanmıyor; "
                     "gider ertelemesi ya da ek finansman gerekir.")
        st.write(text)
    labels = sorted(set(res["outflows"]["label"].dropna())) if "label" in res["outflows"] else []
    actionable_ids = list(res["ranked"].loc[res["ranked"]["actionable"], "invoice_id"])
    s1, s2, s3 = st.columns(3)
    top_k = s1.slider("Bir haftada tahsil edilen öncelikli fatura sayısı", 0, min(40, len(actionable_ids)), 0)
    delayed = s2.multiselect("Ertelenecek gider kalemleri", labels)
    delay_days = s3.slider("Erteleme (gün)", 0, 60, 0, step=5)
    if top_k or (delayed and delay_days):
        alt = run_scenario(res_key, res, tuple(actionable_ids[:top_k]), tuple(delayed), delay_days)
        fig2 = go.Figure()
        fig2.add_scatter(x=sim.dates, y=sim.p10, name="Kötümser, bugünkü durum", line=dict(color="crimson", dash="dot"))
        fig2.add_scatter(x=alt.dates, y=alt.p10, name="Kötümser, senaryo", line=dict(color="crimson"))
        fig2.add_scatter(x=alt.dates, y=alt.p50, name="Orta tahmin (P50), senaryo", line=dict(color="rgb(31,119,180)"))
        fig2.add_hline(y=0, line_dash="dash", line_color="gray")
        fig2.update_layout(height=320, margin=dict(l=0, r=0, t=10, b=0), yaxis_title="Kasa (TL)", hovermode="x unified")
        turkish_axes(fig2)
        st.plotly_chart(fig2, width="stretch")
        st.write(f"Senaryoda 90 günde eksiye düşme olasılığı: **%{alt.prob_any_breach * 100:.0f}** "
                 f"(bugünkü durumda %{sim.prob_any_breach * 100:.0f}).")

    st.subheader("Büyük müşteri geç öderse")
    if sim.paths is not None:
        open_ar = (res["obs"][res["obs"]["open_amount"] > 0].groupby("customer_name")["open_amount"].sum()
                   .sort_values(ascending=False))
        name_to_id = res["obs"].drop_duplicates("customer_name").set_index("customer_name")["customer_id"]
        c1, c2 = st.columns([3, 1])
        chosen = c1.multiselect("Müşteri", list(open_ar.index), default=list(open_ar.index[:1]),
                                format_func=lambda n: f"{n} ({tl(open_ar[n], compact=True)})",
                                help="Varsayılan: açık alacağı en büyük müşteri.")
        shock = c2.slider("Ek gecikme (gün)", 0, 90, 30, step=5)
        if chosen and shock:
            cd = run_customer_delay(res_key, res, tuple(name_to_id[n] for n in chosen), shock)
            st.write(f"Seçilen müşterilerin bugün açık **{tl(cd['amount'])}** alacağı {shock} gün daha geç gelirse: "
                     f"90 günde eksiye düşme olasılığı **%{cd['prob_any_breach'] * 100:.0f}** "
                     f"(bugün %{sim.prob_any_breach * 100:.0f}); kötümser en düşük kasa "
                     f"**{tl(cd['p10_min'])}** (bugün {tl(cd['p10_min_before'])}).")
            fig3 = go.Figure()
            fig3.add_scatter(x=sim.dates, y=sim.p10, name="Kötümser, bugünkü durum", line=dict(color="crimson", dash="dot"))
            fig3.add_scatter(x=sim.dates, y=cd["p10"], name="Kötümser, müşteri gecikirse", line=dict(color="crimson"))
            fig3.add_scatter(x=sim.dates, y=cd["p50"], name="Orta tahmin (P50), müşteri gecikirse",
                             line=dict(color="rgb(31,119,180)"))
            fig3.add_hline(y=0, line_dash="dash", line_color="gray")
            fig3.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0), yaxis_title="Kasa (TL)", hovermode="x unified")
            turkish_axes(fig3)
            st.plotly_chart(fig3, width="stretch")

    exposure = pipeline.fx_exposure(res)
    if len(exposure) and sim.paths is not None:
        st.subheader("Kur değişirse")
        show_table(exposure.rename(columns={"currency": "Para birimi", "original": "Açık alacak (döviz)",
                                            "rate": "Girilen kur", "tl": "TL karşılığı (TL)"}),
                   width="stretch", hide_index=True)
        pct = st.slider("TL'nin dövizlere karşı değişimi (%)", -30, 50, 10, step=5,
                        help="Artı: TL değer kaybeder, dövizli alacağın TL karşılığı artar. Kur tahmini değildir; "
                             "kendi senaryonuzu girersiniz. Dövizli borçlar kapsam dışıdır.")
        if pct:
            fxs = run_fx_shift(res_key, res, pct / 100)
            st.write(f"Kur %{pct:+d} değişirse: 90 günde eksiye düşme olasılığı **%{fxs['prob_any_breach'] * 100:.0f}** "
                     f"(bugün %{sim.prob_any_breach * 100:.0f}); kötümser en düşük kasa **{tl(fxs['p10_min'])}** "
                     f"(bugün {tl(fxs['p10_min_before'])}).")

with tab_accuracy:
    info = res["info"]
    st.write("**Bu tahmin neye dayanıyor?**")
    st.write(f"• {info['n_invoices']} fatura, {info['n_customers']} müşteri; geçmiş {info['history_from']:%d.%m.%Y} tarihinden başlıyor.")
    st.write(f"• Ödeme davranışını öğrenmek için vadesi dolmuş {info['n_train']} fatura kullanıldı"
             + (" (az olduğu için basit yöntem: müşterinin geçmiş medyanı)." if info["simple_model"]
                else " (LightGBM kantil regresyonu ile müşterinin geçmiş medyanının birleşimi)."))
    st.write(f"• Tahmin aralığının genişliği, sistemin geçmiş dört çeyrekte {info['n_calibration']} faturada yaptığı "
             "ileriye dönük tahminlerin hatasından ayarlandı."
             + (" Bu sayı az; aralıklar varsayılan değerlere yakın." if info["n_calibration"] < 100 else ""))
    if info.get("sales_method"):
        spread = info.get("sales_error_spread")
        st.write("• Yeni satışlar: " + ("geçen yılın aynı dönemi esas alındı (işletmenizin geçmişinde son dönemin hızından "
                                         "anlamlı biçimde daha isabetliydi)" if info["sales_method"] == "mevsimsel"
                                         else "son dönemin satış hızı esas alındı")
                 + (f"; belirsizliği kendi geçmiş satış tahmini hatalarınızdan ({info['sales_errors_n']} hafta) geliyor."
                    if spread is not None else "; geçmiş az olduğu için belirsizlik faturaların yeniden örneklenmesiyle verildi."))
        if info["sales_method"] == "hiz" and (res["as_of"] - info["history_from"]).days < 395:
            st.warning("Satış geçmişiniz bir yıldan kısa: mevsimsellik bilinemiyor. Yoğun sezonun hemen ardından yeni satış "
                       "tahmini iyimser kalabilir (gerçek bir KOBİ verisinde bu durumda kötümser uç beklenenden sık aşıldı). "
                       "Kararı kötümser çizgiye göre verin ya da 'Gelecek satışları hesaba kat' seçeneğini kapatın.")
    st.write(f"• Müşterilerin birlikte gecikme eğilimi: piyasa geneli {info['rho_market']:.2f}, aynı müşterinin faturaları "
             f"{info['rho_customer']:.2f} (0 = bağımsız, 1 = tamamen birlikte).")
    if info.get("cheque_share"):
        st.write(f"• Son bir yılda faturaların %{info['cheque_share'] * 100:.0f}'i çekle kapandı (ortanca çek vadesi "
                 f"{info['cheque_median_term']:.0f} gün). Bu müşterilerin açık faturaları ve yeni satışları için para, "
                 "fatura kapandığı gün değil çek vadesinde ve karşılıksız çıkma olasılığıyla kasaya sayıldı.")
    if info.get("installment_share"):
        st.write(f"• Son bir yılda kapanan faturaların %{info['installment_share'] * 100:.0f}'i birden çok tahsilatla "
                 "(taksitle) kapandı. Bu müşterilerin henüz ödenmemiş faturalarında ilk taksit, kendi geçmişlerindeki "
                 "oran ve zamanlamayla kapanıştan önce kasaya sayıldı.")
    widen = info.get("widen", 1.0)
    w_lo, w_hi = (widen, widen) if np.isscalar(widen) else widen
    if (w_lo, w_hi) != (1.0, 1.0):
        st.write(f"• Aralık işletmenin kendi geçmiş hatalarına göre ayarlandı: kötümser taraf {w_lo:.2f}, iyimser taraf "
                 f"{w_hi:.2f} kat (1 = değişiklik yok). Pilot kayıtları biriktikçe iki taraf ayrı ayrı güncellenir.")
    st.divider()
    st.write("Geçmişteki birkaç tarihe dönülür, o gün eldeki bilgiyle 90 günlük tahsilat tahmin edilir "
             "ve sonradan gerçekleşenle karşılaştırılır.")
    if st.button("Geri testi çalıştır"):
        bt = run_backtest(res["obs"], res["as_of"])
        if bt is None:
            st.info("Geri test için yeterli geçmiş yok: en az 9 aylık fatura ve ödeme kaydı gerekir.")
        else:
            st.write(f"{len(bt)} test tarihinin {int(bt['inside'].sum())} tanesinde gerçekleşen tahsilat, "
                     f"tahmin bandının içinde kaldı. Orta tahminin (P50) ortalama sapması: "
                     f"%{bt['err_p50_pct'].mean():+.0f}.")
            mae = {k: bt[c].abs().mean() for k, c in (("model", "err_p50_pct"), ("vade", "err_due_pct"),
                                                      ("medyan", "err_median_pct"), ("oran", "err_rate_pct"))}
            better = mae["model"] < min(mae["vade"], mae["medyan"], mae["oran"])
            st.write(f"Basit yöntemlerle karşılaştırma (ortalama mutlak sapma): model %{mae['model']:.0f}, "
                     f"\"her fatura vadesinde ödenir\" %{mae['vade']:.0f}, \"müşteri her zamanki kadar geç öder\" "
                     f"%{mae['medyan']:.0f}, \"son dönemin tahsilat oranı sürer\" %{mae['oran']:.0f}. "
                     + ("Model sizin verinizde basit yöntemlerden daha isabetli." if better else
                        "**Model sizin verinizde basit yöntemlerden daha isabetli değil;** tahminlere temkinli yaklaşın."))
            band = standards.interval_report(bt["actual"], bt["p10"], bt["p90"])
            acc = pilot.accuracy_test(pd.DataFrame({
                "model": (bt["p50"] - bt["actual"]).abs(), "vade": (bt["naive_due"] - bt["actual"]).abs(),
                "medyan": (bt["naive_median"] - bt["actual"]).abs(), "oran": (bt["naive_rate"] - bt["actual"]).abs()}),
                overlap=3)
            st.write(f"Uluslararası testler ({len(bt)} tarih): kötümser uç için Basel Komitesi trafik ışığı "
                     f"**{band['basel_lower']['zone']}** ({band['below']} aşım); Kupiec kapsama testi p = "
                     f"{band['kupiec_central']['p_value']:.2f} ({'reddedildi' if band['kupiec_central']['reject'] else 'reddedilmedi'}); "
                     f"isabet (Diebold-Mariano): **{acc['sonuc']}**.")
            st.caption("Az sayıda tarihle testlerin gücü düşüktür: 'yeşil' ve 'reddedilmedi', modelin doğru olduğunu "
                       "değil, aksine kanıt bulunmadığını gösterir. Pilot süresince kayıtlar biriktikçe güç artar.")
            show_table(bt.rename(columns={
                "origin": "Tahmin tarihi", "actual": "Gerçekleşen (TL)", "p10": "Kötümser (TL)",
                "p50": "Orta tahmin (TL)", "p90": "İyimser (TL)", "inside": "Bant içinde",
                "err_p50_pct": "Sapma (%)", "naive_due": "Vade yöntemi (TL)", "naive_median": "Medyan yöntemi (TL)",
                "err_due_pct": "Vade yöntemi sapma (%)", "err_median_pct": "Medyan yöntemi sapma (%)",
                "naive_rate": "Oran yöntemi (TL)", "err_rate_pct": "Oran yöntemi sapma (%)"}).assign(**{"Tahmin tarihi": lambda d: pd.to_datetime(d["Tahmin tarihi"])}),
                width="stretch", hide_index=True)
    st.divider()
    st.write("**Pilot raporu.** Tek sayfalık, yazdırılabilir özet: kasa bandı, 13 haftalık plan, öncelikli tahsilat ve "
             "tahminin bu işletmenin geçmişinde basit yöntemlere karşı ne kadar tuttuğu.")
    hide = st.checkbox("Müşteri ve işletme adlarını gizle (rapor paylaşılacaksa)", True)
    if st.button("Pilot raporunu hazırla"):
        seller_name = (store.get("seller", "") if own else "Demo şirket") or "İşletme"
        label = anonymize.firm_alias(secret_key(store), seller_name) if hide and own else seller_name
        page = run_pilot(res_key, res, label, hide)
        store.audit("pilot raporu hazırlandı", "adlar gizli" if hide else "adlar açık")
        st.download_button("Raporu indir (HTML; tarayıcıda açıp yazdırabilirsiniz)", page,
                           f"pilot_raporu_{pd.Timestamp(res['as_of']):%Y%m%d}.html", "text/html")
    records = store.pilot_records() if own else pd.DataFrame()
    if len(records):
        with st.expander(f"Pilot kayıtları: {records['as_of'].nunique()} hafta"):
            reason = pilot.record_due(records, res["as_of"], res.get("last_activity"))
            if reason:
                st.caption(reason)
            detail, summary = pilot.score(pilot.records_from_table(records), res["obs"], events=res.get("events"))
            if len(summary):
                st.write("Süresi dolan kayıtlarda tahmin ile gerçekleşen (sapma ve aralık skoru: düşük iyi). "
                         "Tahsilat: açık faturalardan gelen para, kısmi ödemeler dahil. Kasa: o gün girdiğiniz "
                         "kasa ve banka toplamı.")
                verdict = {True: "geçti", False: "kaldı", None: "değerlendirilemedi"}
                view = summary.assign(
                    hedef=summary["hedef"].map({"tahsilat": "Tahsilat", "kasa": "Kapanış kasası"}),
                    fark_guven_araligi=summary["fark_guven_araligi"].map(
                        lambda v: f"{v[0]:+.1f} / {v[1]:+.1f} puan" if isinstance(v, tuple) else "az kayıt"),
                    **{c: summary[c].map(lambda v: verdict.get(v if isinstance(v, bool) else None, "–"))
                       for c in ("B1", "B2") if c in summary})
                show_table(view.rename(columns={
                    "hedef": "Hedef", "ufuk_gun": "Ufuk (gün)", "kayit": "Kayıt", "uyarili_kayit": "Uyarılı (dışarıda)",
                    "sapma_model_%": "Model (%)", "sapma_medyan_%": "Müşteri medyanı (%)",
                    "sapma_oran_%": "Tahsilat oranı (%)", "sapma_vade_%": "Vadesinde öder (%)",
                    "sapma_sabit_%": "Kasa değişmez (%)", "bant_ici": "Bant içinde",
                    "bant_genisligi_%": "Bant genişliği (%)", "aralik_skoru_%": "Aralık skoru (%)",
                    "fark_guven_araligi": "Model eksi en iyi basit yöntem, %90 aralık",
                    "dm_sonuc": "İsabet testi (Diebold-Mariano)", "alt_asim": "Kötümserin altı (adet)",
                    "ust_asim": "İyimserin üstü (adet)", "basel_alt": "Basel bölgesi (alt uç)",
                    "kupiec_p": "Kupiec p değeri", "B1": "B1 (isabet)", "B2": "B2 (aralık)"}),
                    width="stretch", hide_index=True)
                st.caption("Ölçütler uluslararası standartlardır, kendi eşiğimiz yoktur. B1: Diebold-Mariano testi "
                           "(Harvey-Leybourne-Newbold düzeltmesi, %5): model basit yöntemlerden anlamlı biçimde kötü "
                           "değilse geçer. B2: kötümser uç için Basel Komitesi trafik ışığı (BIS 1996) yeşil ve Kupiec "
                           "(1995) kapsama testleri reddetmiyorsa geçer. Haftalık kayıtların ufukları üst üste bindiği "
                           "için kayıtlar bağımsız sayılmaz; testler bunu hesaba katar.")
            else:
                st.caption("Henüz süresi dolan kayıt yok: ilk karşılaştırma, ilk kayıttan 7–14 gün sonra yapılır.")
            show_table(records.drop(columns=["created", "meta"]).rename(columns={
                "as_of": "Kayıt tarihi", "target": "Hedef", "horizon": "Ufuk (gün)", "until": "Ufkun sonu",
                "p10": "Kötümser (TL)", "p50": "Orta tahmin (TL)", "p90": "İyimser (TL)",
                "naive_due": "Vadesinde öder (TL)", "naive_median": "Müşteri medyanı (TL)",
                "naive_rate": "Tahsilat oranı (TL)", "naive_flat": "Kasa değişmez (TL)", "opening": "O günkü kasa (TL)"}),
                width="stretch", hide_index=True)

    if own:
        with st.expander("İşlem kayıtları (son 200)"):
            st.caption("Yükleme, takma adlı paket, yedek, geri yükleme, silme ve giriş denemeleri buraya yazılır; "
                       "uygulama içinden silinemez (KVKK Kişisel Veri Güvenliği Rehberi: log kayıtları).")
            show_table(store.audit_log().rename(columns={"ts": "Zaman", "action": "İşlem", "detail": "Ayrıntı",
                                                         "user": "Windows kullanıcısı"}),
                       width="stretch", hide_index=True)

with tab_collect:
    st.subheader("Öncelikli tahsilat listesi")
    ranked = res["ranked"]
    todo = ranked[ranked["actionable"]].copy()
    todo["payday_label"] = [actions.payday_label(d, w) for d, w in zip(todo["payday"], todo["payweekday"])]
    todo["stage_label"] = todo["stage"].map(STAGES)
    impact = run_impact(res_key, res, tuple(todo["invoice_id"].head(30)))
    todo["impact"] = todo["invoice_id"].astype(str).map(impact)
    show_table(
        todo[["invoice_id", "customer_name", "due_date", "open_amount", "days_overdue", "p_late", "impact", "stage_label",
              "payday_label", "contact_date"]].rename(columns={
            "impact": "Gelmezse en düşük kasa düşüşü (TL)",
            "invoice_id": "Fatura", "customer_name": "Müşteri", "due_date": "Vade", "open_amount": "Tutar (TL)",
            "days_overdue": "Gecikme (gün)", "p_late": "Risk", "stage_label": "Aşama",
            "payday_label": "Müşterinin ödeme günü", "contact_date": "Önerilen iletişim tarihi"}),
        help={"Risk": "Kasa açığı oluşmadan önce bu faturanın ödenmemiş olma olasılığı. Liste, tutar × risk'e göre sıralıdır.",
              "Gecikme (gün)": "Vadeden bu yana geçen gün. Eksi değer: vadesine kalan gün.",
              "Aşama": "Hatırlatma: vadesine 7 günden az kaldı. Mutabakat: 1-15 gün gecikmiş. Resmî bildirim: 15 günden fazla.",
              "Müşterinin ödeme günü": "Müşteri ödemelerini düzenli olarak belli bir günde yapıyorsa o gün.",
              "Gelmezse en düşük kasa düşüşü (TL)": "Bu fatura 90 gün içinde hiç gelmezse, kötümser senaryodaki en "
                                                    "düşük kasanın ne kadar azalacağı (listenin ilk 30 faturası için)."},
        width="stretch", hide_index=True)

    conc = actions.concentration(res["obs"])
    if conc["top_share"] >= 0.5:
        st.warning(f"Açık alacağın %{conc['top_share'] * 100:.0f}'i üç müşteride: {', '.join(conc['top_names'])}. "
                   f"Alacak, eşit büyüklükte yalnızca {conc['effective_n']:.1f} müşteriye yayılmış gibi; bu müşterilerden "
                   "birinin gecikmesi kasayı tek başına belirler.")
    unmatched = res.get("unmatched")
    if own and unmatched is not None and len(unmatched):
        with st.expander(f"Eşleşmeyen banka tahsilatları: {len(unmatched)} adet, {tl(unmatched['amount'].sum())}"):
            st.write("Bu girişlerin hangi müşteriden geldiği bulunamadı. Bir kez müşteriye bağlarsanız aynı gönderen "
                     "bundan sonraki ekstrelerde otomatik tanınır.")
            show = unmatched.reset_index(drop=True)
            show_table(show[["date", "amount", "description"]].rename(columns={
                "date": "Tarih", "amount": "Tutar (TL)", "description": "Açıklama"}), width="stretch")
            row = st.number_input("Satır no", 0, len(show) - 1, 0)
            names = res["obs"].drop_duplicates("customer_id").set_index("customer_id")["customer_name"]
            target = st.selectbox("Müşteri", names.index, format_func=lambda c: names[c])
            key = sender_key(show.at[int(row), "description"])
            st.caption(f"Tanınacak gönderen: \"{key}\"")
            if key and st.button("Bu göndereni müşteriye bağla"):
                aliases = json.loads(store.get("sender_aliases", "{}"))
                aliases[key] = str(target)
                store.set("sender_aliases", json.dumps(aliases, ensure_ascii=False))
                st.rerun()

    if own:
        outcomes = actions.message_outcomes(store.events(), res["obs"], res["as_of"])
        if len(outcomes):
            paid14 = (outcomes["Durum"] == "14 gün içinde ödendi").mean()
            with st.expander(f"Gönderilen mesajların sonucu: {len(outcomes)} mesaj, %{paid14 * 100:.0f}'i 14 gün içinde ödendi"):
                st.caption("Bu bir etki ölçümü değildir: mesaj olmasa da ödenecek faturalar da burada görünür. "
                           "Mesajın gerçek etkisi, ancak benzer faturalarla karşılaştırarak ölçülebilir.")
                show_table(outcomes, width="stretch", hide_index=True)

    doubtful = ranked[ranked["stage"] == "supheli"]
    if len(doubtful):
        with st.expander(f"Tahsili zor görünen alacaklar: {len(doubtful)} fatura, {tl(doubtful['open_amount'].sum())}"):
            st.write(f"Bu faturalar {actions.DOUBTFUL_MIN_OVERDUE} günden fazla gecikmiş ve geçmiş verinize göre önümüzdeki "
                     f"90 günde tahsil edilme olasılıkları %{actions.DOUBTFUL_MAX_COLLECT_PROB * 100:.0f}'in altında. "
                     "Hatırlatma listesinde gösterilmezler; yeni bir hatırlatma yerine hukuki yolları değerlendirin.")
            st.caption("Bu, geçmiş verinize dayanan istatistiksel bir sınıflamadır. Vergi bakımından \"şüpheli alacak\" "
                       "sayılması ve karşılık ayrılması ayrı şartlara bağlıdır (VUK m.323: dava veya icra safhasında olmak "
                       "ya da protestoya veya yazıyla birden fazla istenmesine rağmen ödenmemiş olup belirlenen tutarı "
                       "aşmamak). Muhasebe kaydını mali müşavirinizle değerlendirin.")
            show_table(doubtful[["invoice_id", "customer_name", "due_date", "open_amount", "days_overdue", "p_collect"]]
                         .rename(columns={"invoice_id": "Fatura", "customer_name": "Müşteri", "due_date": "Vade",
                                          "open_amount": "Tutar (TL)", "days_overdue": "Gecikme (gün)",
                                          "p_collect": "90 günde tahsil olasılığı"}), width="stretch", hide_index=True)
            if own:
                gone = st.selectbox("Tahsil edilemez sayılacak fatura", doubtful["invoice_id"], key="writeoff_pick")
                if st.button("Tahsil edilemez olarak kaydet",
                             help="Fatura açık alacaktan ve kasa tahmininden çıkar; ödenmiş sayılmaz. Yalnızca bu panelin "
                                  "tahminini etkiler, muhasebe kaydı değildir. Şüpheli alacak karşılığı (VUK m.323) ya da "
                                  "değersiz alacak (VUK m.322) kararı mali müşavirinizle verilmelidir. Geri alınabilir."):
                    record(gone, "writeoff", "1")
    if own and "written_off" in res["obs"] and res["obs"]["written_off"].any():
        lost = res["obs"][res["obs"]["written_off"]]
        with st.expander(f"Tahsil edilemez sayılanlar: {len(lost)} fatura, {tl(lost['amount'].sum())}"):
            show_table(lost[["invoice_id", "customer_name", "due_date", "amount"]].rename(columns={
                "invoice_id": "Fatura", "customer_name": "Müşteri", "due_date": "Vade", "amount": "Tutar (TL)"}),
                width="stretch", hide_index=True)
            back = st.selectbox("Geri alınacak fatura", lost["invoice_id"], key="writeoff_undo")
            if st.button("Tahsil edilemez kaydını kaldır"):
                record(back, "writeoff", "0")

    st.subheader("Mesaj taslağı")
    if len(todo):
        by_id = todo.set_index("invoice_id", drop=False)
        pick = st.selectbox("Fatura", todo["invoice_id"], format_func=lambda i: f"{i} · {by_id.at[i, 'customer_name']}")
        draft = actions.draft_message(by_id.loc[pick], seller, *((iban, bank) if own else ("", "")))
        body = st.text_area("Taslak (düzenleyebilirsiniz)", draft["body"], height=140, key=f"draft_{pick}")
        identity = actions.sender_identity_problem(seller)
        if identity:
            st.error(identity + " Kimlik tamamlanana kadar gönderme düğmeleri kapalıdır.")
        st.warning(actions.FORMAL_NOTICE_WARNING)
        if draft["note"]:
            st.info(draft["note"])
        if own:
            st.caption("Mesajı kendi e-posta ya da WhatsApp hesabınızdan gönderdikten sonra aşağıdan kayda geçirin. "
                       f"Kayda geçen fatura {actions.CONTACT_COOLDOWN_DAYS} gün boyunca listede yeniden önerilmez.")
            owner = st.text_input("Takipten sorumlu kişi (isteğe bağlı)", store.get("last_owner", ""), key=f"owner_{pick}",
                                  help="Kayda yazılır; birden çok kişi tahsilat yapıyorsa kimin takip ettiği görünür.")
            tag = f"[sorumlu: {owner.strip()}] " if owner.strip() else ""
            if owner.strip():
                store.set("last_owner", owner.strip())
            phones = res["obs"].set_index("invoice_id")["phone"] if "phone" in res["obs"] else {}
            phone = ingest.normalize_phone(st.text_input("Müşterinin cep telefonu (WhatsApp)", phones.get(pick, ""),
                                                         key=f"tel_{pick}", placeholder="05XX XXX XX XX"))
            if phone and not identity:
                st.link_button("WhatsApp'ta taslağı aç", actions.whatsapp_link(phone, body))
                st.caption("WhatsApp kendi hesabınızda, mesaj yazılmış hâlde açılır; gönderdikten sonra aşağıdan kayda geçirin.")
            if mail.ready:
                emails = res["obs"].set_index("invoice_id")["email"] if "email" in res["obs"] else {}
                to = st.text_input("Alıcı e-posta adresi", emails.get(pick, ""), key=f"to_{pick}")
                if st.button("E-posta ile gönder", disabled=not mailer.is_address(to) or bool(identity)):
                    try:
                        mailer.send(mail, to, draft["subject"], body)
                    except mailer.MailError as err:
                        st.error(str(err))
                    else:
                        record(pick, "message", f"{tag}[e-posta: {to.strip()}] {body}")
            b1, b2, b3 = st.columns(3)
            if b1.button("Gönderildi olarak kaydet"):
                record(pick, "message", tag + body)
            if b2.button("Müşteri itiraz etti"):
                record(pick, "dispute", "1")
            promise = b3.date_input("Ödeme sözü tarihi", value=None, format="DD.MM.YYYY", key=f"promise_{pick}")
            if promise and b3.button("Ödeme sözünü kaydet"):
                record(pick, "promise", str(promise))
    else:
        st.write("Şu an hatırlatma gerektiren fatura yok.")

    if own:
        obs = res["obs"]
        held = obs[(obs["open_amount"] > 0) & (obs["disputed"] | (obs["promised_date"] > res["as_of"]))]
        waiting = ranked[ranked["last_contact"].notna() & ~ranked["actionable"]]
        with st.expander(f"Beklemedeki faturalar ({len(held) + len(waiting)})"):
            if len(held):
                st.write("İtirazlı ya da ödeme sözü verilmiş faturalar:")
                show_table(held[["invoice_id", "customer_name", "open_amount", "disputed", "promised_date"]].rename(columns={
                    "invoice_id": "Fatura", "customer_name": "Müşteri", "open_amount": "Tutar (TL)",
                    "disputed": "İtirazlı", "promised_date": "Ödeme sözü"}), width="stretch", hide_index=True)
                undo = st.selectbox("Durumu kaldırılacak fatura", held["invoice_id"])
                u1, u2 = st.columns(2)
                if u1.button("İtirazı kaldır"):
                    record(undo, "dispute", "0")
                if u2.button("Ödeme sözünü kaldır"):
                    record(undo, "promise", "")
            if len(waiting):
                st.write("Yakın zamanda yazılmış, yanıt beklenen faturalar:")
                show_table(waiting[["invoice_id", "customer_name", "open_amount", "last_contact"]].rename(columns={
                    "invoice_id": "Fatura", "customer_name": "Müşteri", "open_amount": "Tutar (TL)",
                    "last_contact": "Son iletişim"}), width="stretch", hide_index=True)
            if not len(held) and not len(waiting):
                st.write("Beklemede fatura yok.")
