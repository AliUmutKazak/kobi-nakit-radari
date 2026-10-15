"""Yönetici paneli: streamlit run app.py"""
import hashlib
import io
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, "src")

import pandas as pd  # noqa: E402
import plotly.graph_objects as go  # noqa: E402
import streamlit as st  # noqa: E402

from radar import actions, anonymize, ingest, mailer, pilot, pipeline  # noqa: E402
from radar.reconcile import reconcile, sender_key  # noqa: E402
from radar.store import Store, create_business, list_businesses  # noqa: E402

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
            df[col] = df[col].round(0)
            config[col] = st.column_config.NumberColumn(col, format="localized", help=tip)
        elif "olasılı" in col.lower() or "risk" in col.lower():
            df[col] = df[col].round(2)
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
           "Nasıl kullanılacağı: proje klasöründeki docs/KULLANIM_KILAVUZU.md")


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
    ledger_cheques = []
    for u in uploads:
        if not u.name.lower().endswith(".xml") and ingest.is_ledger(_open(u)):
            df, n, chq = ingest.load_ledger(_open(u), terms, fallback_customer=Path(u.name).stem)
            frames.append(df)
            notes += n
            ledger_cheques.append(chq)
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
    return pd.concat(frames, ignore_index=True).drop_duplicates("invoice_id"), notes


@st.cache_data(show_spinner="Demo şirketin 90 günlük kasası hesaplanıyor; 10-20 saniye sürer. Panel açık kaldıkça sonraki işlemler anında gelir...")
def run_demo(seed: int, include_projected: bool):
    res = pipeline.demo(seed=seed, include_projected=include_projected)
    return {k: res[k] for k in KEEP} | {"notes": [], "has_outflows": True, "unmatched": None, "last_activity": None}


@st.cache_data(show_spinner="Verileriniz işleniyor ve 90 günlük kasa hesaplanıyor; 10-20 saniye sürebilir. Veri değişmedikçe sonraki işlemler anında gelir...")
def run_own(path: str, rev: int, as_of: str, include_projected: bool):
    """`rev` kayıt her değiştiğinde artar; sonuç ancak o zaman yeniden hesaplanır. `path` işletmeyi ayırır."""
    store = get_store(path)
    notes = [n for name in ("invoices", "payments", "payables") for n in json.loads(store.get(f"notes_{name}", "[]"))]
    obs = store.apply_events(store.load("invoices"), as_of)
    obs = obs[obs["issue_date"] <= pd.Timestamp(as_of)]
    payments = store.load("payments")
    if payments is not None:
        payments = payments[payments["date"] <= pd.Timestamp(as_of)]
        obs, _, unmatched = reconcile(obs, payments, aliases=json.loads(store.get("sender_aliases", "{}")))
        notes.append(f"Ekstre: {len(payments)} tahsilatın {len(payments) - len(unmatched)} tanesi faturalarla eşleşti.")
        if len(unmatched):
            notes.append(f"Eşleşmeyen tahsilat tutarı: {tl(unmatched['amount'].sum())} "
                         "(müşterisi bulunamayan ya da fazla ödeme).")
    outflows, cheques, payables = store.load("outflows"), store.load("cheques"), store.load("payables")
    notes += json.loads(store.get("notes_cheques", "[]"))
    fixed = {k: float(store.get(f"fixed_{k}", 0)) for k in ("payroll", "muhtasar", "sgk", "kdv", "rent")}
    if any(fixed.values()):
        plan = ingest.fixed_cost_plan(as_of, payroll_day=int(float(store.get("fixed_payroll_day", 1))),
                                      rent_day=int(float(store.get("fixed_rent_day", 1))), **fixed)
        notes.append(f"Aylık sabit giderlerden {len(plan)} ödeme ({tl(plan['amount'].sum())}) eklendi.")
        outflows = plan if outflows is None else pd.concat([outflows, plan], ignore_index=True)
    if payables is not None:
        flows, n = ingest.payables_to_outflows(payables, as_of)
        notes += n + [f"Ödenecek faturalar: {len(payables)} adet, {tl(payables['amount'].sum())}."]
        outflows = flows if outflows is None else pd.concat([outflows, flows], ignore_index=True)
    if cheques is not None:
        notes.append(f"Çek/senet portföyü: {len(cheques)} adet, {tl(cheques['amount'].sum())}.")
    res = pipeline.forecast(obs.reset_index(drop=True), as_of, float(store.get("opening", 0)),
                            outflows if outflows is not None else pd.DataFrame({"date": [], "amount": []}),
                            include_projected=include_projected, cheques=cheques)
    # Verideki son hareket: bundan sonraki ödemeler bilinmez, ödenmemiş görünür.
    dates = [obs["issue_date"].max(), obs["paid_date"].max()] + ([payments["date"].max()] if payments is not None else [])
    last = max(d for d in dates if pd.notna(d))
    return {k: res[k] for k in KEEP} | {"notes": notes, "has_outflows": outflows is not None,
                                        "unmatched": unmatched if payments is not None else None, "last_activity": last,
                                        "n_payments": len(payments) if payments is not None else None}


@st.cache_data(show_spinner="Açığı kapatacak tahsilat hesaplanıyor...")
def run_gap(key, _res):
    return pipeline.gap_summary(_res)


@st.cache_data(show_spinner=False)
def run_scenario(key, _res, collect_ids, delay_labels, delay_days):
    return pipeline.scenario(_res, collect_ids, delay_labels=delay_labels, delay_days=delay_days)


@st.cache_data(show_spinner="Geçmiş tarihlere dönülüp tahmin yeniden üretiliyor; yarım dakikayı bulabilir...")
def run_backtest(obs, as_of):
    return pipeline.backtest_own(obs, as_of)


@st.cache_data(show_spinner="Pilot raporu hazırlanıyor; geçmiş tarihlerde test de yapıldığı için bir dakikayı bulabilir...")
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
        seller = st.text_input("Mesajlardaki imza (ticaret unvanı ve MERSİS no)", "Örnek Ticaret A.Ş.")
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
            if st.session_state.get("business_error"):
                st.error(st.session_state.pop("business_error"))
        has_data = store.load("invoices") is not None
        with st.expander("1. Temel bilgiler", expanded=True):
            as_of = st.date_input("Tahmin tarihi", format="DD.MM.YYYY",
                                  help="Genellikle bugün. Geçmiş bir tarih seçerseniz o güne kadarki veriyle tahmin yapılır.")
            opening = st.number_input("Kasa ve bankadaki toplam para (TL)", 0.0, value=float(store.get("opening", 0)),
                                      step=10_000.0, help="Her kullanımda güncelleyin; tahmin bu tutardan başlar.")
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
                                   help="Ticari iletilerde gönderenin kimliği açıkça yazılmalıdır.")
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
        with st.expander("5. Pilot: anonim veri paketi"):
            st.write("Yüklediğiniz dosyaların, müşteri adları ve vergi numaraları takma adlarla değiştirilmiş bir "
                     "kopyası. Tutar ve tarihler aynen kalır; e-posta ve telefon silinir; banka açıklamaları tümüyle "
                     "yeniden yazılır. Pilot çalışması için paylaşılacak dosya budur.")
            if has_data and st.button("Anonim paketi hazırla"):
                blob, summary = anonymous_package(store, seller)
                st.download_button("Paketi indir (zip)", blob, f"{summary['işletme_takma_adı']}.zip", "application/zip")
                st.caption(f"{summary['fatura']} fatura, {summary['müşteri']} müşteri, dönem {summary['dönem']}. "
                           "Göndermeden önce zip dosyasını açıp gözle kontrol edin.")
            st.caption(f"Takma adları üreten gizli anahtar yalnızca bu bilgisayarda: {anonymize.key_path()}. "
                       "Anahtar paylaşılmaz; aynı anahtar her ay aynı takma adları verir.")
            pilot_on = st.checkbox("Pilota katılıyorum: her hafta ileriye dönük kaydı kendiliğinden al",
                                   store.get("pilot_on", "0") == "1",
                                   help="Panel haftada bir, bugünün tahmininden önümüzdeki 14 ve 30 günün tahsilat "
                                        "tahminini kaydeder. Kayıtlar değiştirilemez; süre dolunca gerçekleşenle "
                                        "karşılaştırılır ve anonim pakete eklenir.")
            store.set("pilot_on", int(pilot_on))
        with st.expander("Diğer ayarlar"):
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
                    store.set(f"hash_{which}", "")
                    st.rerun()
            st.download_button("Verilerimin yedeğini indir", store.backup_bytes(),
                               f"kobi_radar_yedek_{pd.Timestamp.now():%Y%m%d}.db",
                               help="Tüm yüklenen tablolar, ayarlar ve kayıtlar tek dosyada. Güvenli bir yerde saklayın.")
            st.write("**Kayıtlı veriyi sil.** Yüklenen tablolar silinir; itiraz, ödeme sözü ve mesaj kayıtları korunur.")
            sure = st.checkbox("Eminim")
            if st.button("Tabloları sil", disabled=not sure):
                store.clear()
                for name in ("invoices", "payments", "outflows", "cheques", "payables"):
                    store.set(f"hash_{name}", "")
                st.rerun()

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
    res = run_demo(int(seed), include_projected)
    res_key = ("demo", int(seed), include_projected)
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
if own and store.get("pilot_on", "0") == "1" and pilot.record_due(store.pilot_records(), res["as_of"],
                                                                  res.get("last_activity")) is None:
    with st.spinner("Bu haftanın pilot kaydı alınıyor; yarım dakika kadar sürer..."):
        weekly = pilot.forward_record(res["obs"], res["as_of"])
    if store.add_pilot_record(res["as_of"], weekly):
        st.toast("Bu haftanın pilot kaydı alındı.")
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
            help="Önümüzdeki 90 gün içinde kasanın en az bir gün eksiye düşme olasılığı.")

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

tab_cash, tab_collect, tab_accuracy = st.tabs(["Kasa tahmini", "Tahsilat işleri", "Tahmin doğruluğu"])

with tab_cash:
    fig = go.Figure()
    fig.add_scatter(x=sim.dates, y=sim.p90, line=dict(width=0), showlegend=False, hoverinfo="skip")
    fig.add_scatter(x=sim.dates, y=sim.p10, fill="tonexty", line=dict(width=0), name="Olası aralık (%80)",
                    fillcolor="rgba(31,119,180,0.2)")
    fig.add_scatter(x=sim.dates, y=sim.p50, name="Beklenen", line=dict(color="rgb(31,119,180)"))
    fig.add_hline(y=0, line_dash="dash", line_color="crimson")
    fig.update_layout(height=380, margin=dict(l=0, r=0, t=10, b=0), yaxis_title="Kasa (TL)", hovermode="x unified")
    turkish_axes(fig)
    st.plotly_chart(fig, width="stretch")
    st.caption("Mavi bant: kasanızın %80 olasılıkla içinde kalacağı aralık. Bandın alt kenarı kötümser, üst kenarı "
               "iyimser durumdur. Kırmızı kesikli çizgi sıfır.")
    with st.expander("13 haftalık plan"):
        st.caption("Bilinen çıkışlar (giderler, borçlar) kesin kabul edilir. Tahsilat sütunları tahmindir: açık faturalar "
                   "müşterilerin geçmiş ödeme davranışından, yeni satışlar son 90 günün satış hızından gelir.")
        show_table(pipeline.weekly_table(res), width="stretch", hide_index=True,
                   help={"Eksiye düşme olasılığı": "O hafta içinde kasanın en az bir gün eksiye düşme olasılığı."})

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
        fig2.add_scatter(x=alt.dates, y=alt.p50, name="Beklenen, senaryo", line=dict(color="rgb(31,119,180)"))
        fig2.add_hline(y=0, line_dash="dash", line_color="gray")
        fig2.update_layout(height=320, margin=dict(l=0, r=0, t=10, b=0), yaxis_title="Kasa (TL)", hovermode="x unified")
        turkish_axes(fig2)
        st.plotly_chart(fig2, width="stretch")
        st.write(f"Senaryoda 90 günde eksiye düşme olasılığı: **%{alt.prob_any_breach * 100:.0f}** "
                 f"(bugünkü durumda %{sim.prob_any_breach * 100:.0f}).")

with tab_accuracy:
    info = res["info"]
    st.write("**Bu tahmin neye dayanıyor?**")
    st.write(f"• {info['n_invoices']} fatura, {info['n_customers']} müşteri; geçmiş {info['history_from']:%d.%m.%Y} tarihinden başlıyor.")
    st.write(f"• Ödeme davranışını öğrenmek için vadesi dolmuş {info['n_train']} fatura kullanıldı"
             + (" (az olduğu için basit yöntem: müşterinin geçmiş medyanı)." if info["simple_model"]
                else " (öğrenen model: LightGBM kantil regresyonu)."))
    st.write(f"• Tahmin aralığının genişliği, sistemin geçmiş dört çeyrekte {info['n_calibration']} faturada yaptığı "
             "ileriye dönük tahminlerin hatasından ayarlandı."
             + (" Bu sayı az; aralıklar varsayılan değerlere yakın." if info["n_calibration"] < 100 else ""))
    st.write(f"• Müşterilerin birlikte gecikme eğilimi: piyasa geneli {info['rho_market']:.2f}, aynı müşterinin faturaları "
             f"{info['rho_customer']:.2f} (0 = bağımsız, 1 = tamamen birlikte).")
    st.divider()
    st.write("Geçmişteki birkaç tarihe dönülür, o gün eldeki bilgiyle 90 günlük tahsilat tahmin edilir "
             "ve sonradan gerçekleşenle karşılaştırılır.")
    if st.button("Geri testi çalıştır"):
        bt = run_backtest(res["obs"], res["as_of"])
        if bt is None:
            st.info("Geri test için yeterli geçmiş yok: en az 9 aylık fatura ve ödeme kaydı gerekir.")
        else:
            st.write(f"{len(bt)} test tarihinin {int(bt['inside'].sum())} tanesinde gerçekleşen tahsilat, "
                     f"tahmin bandının içinde kaldı. Beklenen değerin ortalama sapması: "
                     f"%{bt['err_p50_pct'].mean():+.0f}.")
            mae = {k: bt[c].abs().mean() for k, c in (("model", "err_p50_pct"), ("vade", "err_due_pct"),
                                                      ("medyan", "err_median_pct"), ("oran", "err_rate_pct"))}
            better = mae["model"] < min(mae["vade"], mae["medyan"], mae["oran"])
            st.write(f"Basit yöntemlerle karşılaştırma (ortalama mutlak sapma): model %{mae['model']:.0f}, "
                     f"\"her fatura vadesinde ödenir\" %{mae['vade']:.0f}, \"müşteri her zamanki kadar geç öder\" "
                     f"%{mae['medyan']:.0f}, \"son dönemin tahsilat oranı sürer\" %{mae['oran']:.0f}. "
                     + ("Model sizin verinizde basit yöntemlerden daha isabetli." if better else
                        "**Model sizin verinizde basit yöntemlerden daha isabetli değil;** tahminlere temkinli yaklaşın."))
            show_table(bt.rename(columns={
                "origin": "Tahmin tarihi", "actual": "Gerçekleşen (TL)", "p10": "Kötümser (TL)",
                "p50": "Beklenen (TL)", "p90": "İyimser (TL)", "inside": "Bant içinde",
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
        st.download_button("Raporu indir (HTML; tarayıcıda açıp yazdırabilirsiniz)", page,
                           f"pilot_raporu_{pd.Timestamp(res['as_of']):%Y%m%d}.html", "text/html")
    records = store.pilot_records() if own else pd.DataFrame()
    if len(records):
        with st.expander(f"Pilot kayıtları: {records['as_of'].nunique()} hafta"):
            reason = pilot.record_due(records, res["as_of"], res.get("last_activity"))
            if reason:
                st.caption(reason)
            detail, summary = pilot.score(pilot.records_from_table(records), res["obs"])
            if len(summary):
                st.write("Süresi dolan kayıtlarda tahmin ile gerçekleşen tahsilat (sapma: düşük iyi):")
                show_table(summary.rename(columns={
                    "ufuk_gun": "Ufuk (gün)", "kayit": "Kayıt", "sapma_model_%": "Model sapması (%)",
                    "sapma_medyan_%": "Müşteri medyanı (%)", "sapma_oran_%": "Tahsilat oranı (%)",
                    "sapma_vade_%": "Vadesinde öder (%)", "bant_ici": "Bant içinde", "B1_gecti": "B1 geçti",
                    "B2_gecti": "B2 geçti"}), width="stretch", hide_index=True)
            else:
                st.caption("Henüz süresi dolan kayıt yok: ilk karşılaştırma, ilk kayıttan 14 gün sonra yapılır.")
            show_table(records.drop(columns=["created"]).rename(columns={
                "as_of": "Kayıt tarihi", "horizon": "Ufuk (gün)", "until": "Ufkun sonu", "p10": "Kötümser (TL)",
                "p50": "Beklenen (TL)", "p90": "İyimser (TL)", "naive_due": "Vadesinde öder (TL)",
                "naive_median": "Müşteri medyanı (TL)", "naive_rate": "Tahsilat oranı (TL)"}),
                width="stretch", hide_index=True)

with tab_collect:
    st.subheader("Öncelikli tahsilat listesi")
    ranked = res["ranked"]
    todo = ranked[ranked["actionable"]].copy()
    todo["payday_label"] = [actions.payday_label(d, w) for d, w in zip(todo["payday"], todo["payweekday"])]
    todo["stage_label"] = todo["stage"].map(STAGES)
    show_table(
        todo[["invoice_id", "customer_name", "due_date", "open_amount", "days_overdue", "p_late", "stage_label",
              "payday_label", "contact_date"]].rename(columns={
            "invoice_id": "Fatura", "customer_name": "Müşteri", "due_date": "Vade", "open_amount": "Tutar (TL)",
            "days_overdue": "Gecikme (gün)", "p_late": "Risk", "stage_label": "Aşama",
            "payday_label": "Müşterinin ödeme günü", "contact_date": "Önerilen iletişim tarihi"}),
        help={"Risk": "Kasa açığı oluşmadan önce bu faturanın ödenmemiş olma olasılığı. Liste, tutar × risk'e göre sıralıdır.",
              "Gecikme (gün)": "Vadeden bu yana geçen gün. Eksi değer: vadesine kalan gün.",
              "Aşama": "Hatırlatma: vadesine 7 günden az kaldı. Mutabakat: 1-15 gün gecikmiş. Resmî bildirim: 15 günden fazla.",
              "Müşterinin ödeme günü": "Müşteri ödemelerini düzenli olarak belli bir günde yapıyorsa o gün."},
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
        with st.expander(f"Şüpheli alacaklar: {len(doubtful)} fatura, {tl(doubtful['open_amount'].sum())}"):
            st.write(f"Bu faturalar {actions.DOUBTFUL_MIN_OVERDUE} günden fazla gecikmiş ve geçmiş verinize göre önümüzdeki "
                     f"90 günde tahsil edilme olasılıkları %{actions.DOUBTFUL_MAX_COLLECT_PROB * 100:.0f}'in altında. "
                     "Hatırlatma listesinde gösterilmezler; yeni bir hatırlatma yerine hukuki yolları değerlendirin.")
            show_table(doubtful[["invoice_id", "customer_name", "due_date", "open_amount", "days_overdue", "p_collect"]]
                         .rename(columns={"invoice_id": "Fatura", "customer_name": "Müşteri", "due_date": "Vade",
                                          "open_amount": "Tutar (TL)", "days_overdue": "Gecikme (gün)",
                                          "p_collect": "90 günde tahsil olasılığı"}), width="stretch", hide_index=True)

    st.subheader("Mesaj taslağı")
    if len(todo):
        by_id = todo.set_index("invoice_id", drop=False)
        pick = st.selectbox("Fatura", todo["invoice_id"], format_func=lambda i: f"{i} · {by_id.at[i, 'customer_name']}")
        draft = actions.draft_message(by_id.loc[pick], seller, *((iban, bank) if own else ("", "")))
        body = st.text_area("Taslak (düzenleyebilirsiniz)", draft["body"], height=140, key=f"draft_{pick}")
        if draft["note"]:
            st.info(draft["note"])
        if own:
            st.caption("Mesajı kendi e-posta ya da WhatsApp hesabınızdan gönderdikten sonra aşağıdan kayda geçirin. "
                       f"Kayda geçen fatura {actions.CONTACT_COOLDOWN_DAYS} gün boyunca listede yeniden önerilmez.")
            phones = res["obs"].set_index("invoice_id")["phone"] if "phone" in res["obs"] else {}
            phone = ingest.normalize_phone(st.text_input("Müşterinin cep telefonu (WhatsApp)", phones.get(pick, ""),
                                                         key=f"tel_{pick}", placeholder="05XX XXX XX XX"))
            if phone:
                st.link_button("WhatsApp'ta taslağı aç", actions.whatsapp_link(phone, body))
                st.caption("WhatsApp kendi hesabınızda, mesaj yazılmış hâlde açılır; gönderdikten sonra aşağıdan kayda geçirin.")
            if mail.ready:
                emails = res["obs"].set_index("invoice_id")["email"] if "email" in res["obs"] else {}
                to = st.text_input("Alıcı e-posta adresi", emails.get(pick, ""), key=f"to_{pick}")
                if st.button("E-posta ile gönder", disabled=not mailer.is_address(to)):
                    try:
                        mailer.send(mail, to, draft["subject"], body)
                    except mailer.MailError as err:
                        st.error(str(err))
                    else:
                        record(pick, "message", f"[e-posta: {to.strip()}] {body}")
            b1, b2, b3 = st.columns(3)
            if b1.button("Gönderildi olarak kaydet"):
                record(pick, "message", body)
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
