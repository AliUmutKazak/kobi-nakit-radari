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

from radar import actions, ingest, pipeline  # noqa: E402
from radar.reconcile import reconcile  # noqa: E402
from radar.store import Store  # noqa: E402

ROOT = Path(__file__).parent
SAMPLES = ROOT / "ornekler"
KEEP = ("sim", "ranked", "metrics", "opening", "gap_day", "simple_model", "n_train", "disputed_total", "obs", "as_of",
        "ctx", "outflows")
MAPPABLE = {"invoices": ("Fatura dosyası", ingest.INVOICE_FIELDS, ingest.INVOICE_REQUIRED),
            "payments": ("Banka ekstresi", ingest.PAYMENT_FIELDS, ingest.PAYMENT_REQUIRED)}
STAGES = {"hatirlatma": "Hatırlatma", "mutabakat": "Mutabakat", "resmi": "Resmî bildirim"}

st.set_page_config(page_title="KOBİ Nakit Akışı Radarı", layout="wide")
st.title("KOBİ Nakit Akışı Radarı")
st.caption("Mesajlar taslaktır; bu panel hiçbir mesajı kendiliğinden göndermez.")


@st.cache_resource
def get_store() -> Store:
    return Store(os.environ.get("RADAR_DB", ROOT / "data" / "radar.db"))


def _open(upload):
    buf = io.BytesIO(upload.getvalue())
    buf.name = upload.name
    return buf


def save_upload(store: Store, name: str, uploads, parse) -> None:
    """Dosya değiştiyse ayrıştırıp kaydeder; aynı dosya yeniden çizimde tekrar yazılmaz."""
    uploads = [u for u in (uploads if isinstance(uploads, list) else [uploads]) if u]
    if not uploads:
        return
    mapping = store.get(f"map_{name}", "{}")
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


def parse_invoices(uploads, terms):
    frames, notes = [], []
    xml = [_open(u) for u in uploads if u.name.lower().endswith(".xml")]
    for u in uploads:
        if not u.name.lower().endswith(".xml"):
            df, n = ingest.load_invoices(_open(u), terms, json.loads(get_store().get("map_invoices", "{}")))
            frames.append(df)
            notes += n
    if xml:
        df, n = ingest.load_ubl(xml, terms)
        frames.append(df)
        notes += n
    frames = [f for f in frames if len(f)]
    if not frames:
        raise ValueError("Yüklenen dosyalardan okunabilen fatura çıkmadı.")
    return pd.concat(frames, ignore_index=True).drop_duplicates("invoice_id"), notes


@st.cache_data(show_spinner="Simülasyon çalışıyor...")
def run_demo(seed: int, include_projected: bool):
    res = pipeline.demo(seed=seed, include_projected=include_projected)
    return {k: res[k] for k in KEEP} | {"notes": [], "has_outflows": True}


@st.cache_data(show_spinner="Veriler işleniyor ve simülasyon çalışıyor...")
def run_own(rev: int, as_of: str, include_projected: bool):
    """`rev` kayıt her değiştiğinde artar; sonuç ancak o zaman yeniden hesaplanır."""
    store = get_store()
    notes = [n for name in ("invoices", "payments") for n in json.loads(store.get(f"notes_{name}", "[]"))]
    obs = store.apply_events(store.load("invoices"), as_of)
    obs = obs[obs["issue_date"] <= pd.Timestamp(as_of)]
    payments = store.load("payments")
    if payments is not None:
        payments = payments[payments["date"] <= pd.Timestamp(as_of)]
        obs, _, unmatched = reconcile(obs, payments)
        notes.append(f"Ekstre: {len(payments)} tahsilatın {len(payments) - len(unmatched)} tanesi faturalarla eşleşti.")
        if len(unmatched):
            notes.append(f"Eşleşmeyen tahsilat tutarı: {unmatched['amount'].sum():,.0f} TL "
                         "(müşterisi bulunamayan ya da fazla ödeme).")
    outflows, cheques = store.load("outflows"), store.load("cheques")
    if cheques is not None:
        notes.append(f"Çek/senet portföyü: {len(cheques)} adet, {cheques['amount'].sum():,.0f} TL.")
    res = pipeline.forecast(obs.reset_index(drop=True), as_of, float(store.get("opening", 0)),
                            outflows if outflows is not None else pd.DataFrame({"date": [], "amount": []}),
                            include_projected=include_projected, cheques=cheques)
    return {k: res[k] for k in KEEP} | {"notes": notes, "has_outflows": outflows is not None}


@st.cache_data(show_spinner="Senaryolar hesaplanıyor...")
def run_gap(key, _res):
    return pipeline.gap_summary(_res)


@st.cache_data(show_spinner=False)
def run_scenario(key, _res, collect_ids, delay_labels, delay_days):
    return pipeline.scenario(_res, collect_ids, delay_labels=delay_labels, delay_days=delay_days)


@st.cache_data(show_spinner="Geçmiş tarihlerde tahmin üretiliyor...")
def run_backtest(obs, as_of):
    return pipeline.backtest_own(obs, as_of)


store = get_store()
with st.sidebar:
    source = st.radio("Veri", ["Demo şirket", "Kendi verim"])
    include_projected = st.toggle("Henüz kesilmemiş satışları dahil et", True)
    if source == "Demo şirket":
        seed = st.number_input("Örnek şirket", 1, 99, 7)
        seller = st.text_input("Mesajlardaki imza (ticaret unvanı ve MERSİS no)", "Örnek Ticaret A.Ş.")
    else:
        as_of = st.date_input("Bugünün tarihi", format="DD.MM.YYYY")
        opening = st.number_input("Kasadaki ve bankadaki toplam (TL)", 0.0, value=float(store.get("opening", 0)),
                                  step=10_000.0)
        terms = st.number_input("Vadesi yazmayan faturalar için vade (gün)", 0, 365, int(store.get("terms", 30)),
                                help="TTK m.1530: vade yazmıyorsa borçlu, faturayı aldıktan 30 gün sonra temerrüde düşer.")
        seller = st.text_input("Mesajlardaki imza (ticaret unvanı ve MERSİS no)", store.get("seller", ""))
        for key, value in (("opening", opening), ("terms", int(terms)), ("seller", seller)):
            store.set(key, value)
        st.caption("Yüklenen her dosya, o türdeki kayıtlı verinin yerine geçer ve bu bilgisayarda saklanır.")
        save_upload(store, "invoices",
                    st.file_uploader("Kesilen faturalar (CSV / Excel / e-Fatura XML)", ["csv", "xlsx", "xls", "xml"],
                                     accept_multiple_files=True),
                    lambda ups: parse_invoices(ups, int(terms)))
        save_upload(store, "payments", st.file_uploader("Banka ekstresi (isteğe bağlı)", ["csv", "xlsx", "xls"]),
                    lambda ups: ingest.load_payments(_open(ups[0]), json.loads(store.get("map_payments", "{}"))))
        save_upload(store, "outflows", st.file_uploader("Planlı giderler (isteğe bağlı)", ["csv", "xlsx", "xls"]),
                    lambda ups: (ingest.load_schedule(_open(ups[0])), []))
        save_upload(store, "cheques", st.file_uploader("Çek / senet portföyü (isteğe bağlı)", ["csv", "xlsx", "xls"]),
                    lambda ups: (ingest.load_schedule(_open(ups[0]), "drawer"), []))
        with st.expander("Kayıtlı veriyi sil"):
            st.write("Yüklenen tablolar silinir. İtiraz, ödeme sözü ve mesaj kayıtları korunur.")
            sure = st.checkbox("Eminim")
            if st.button("Tabloları sil", disabled=not sure):
                store.clear()
                for name in ("invoices", "payments", "outflows", "cheques"):
                    store.set(f"hash_{name}", "")
                st.rerun()

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
            "Vade Tarihi, VKN, Ödeme Tarihi ve Kalan sütunları varsa kullanılır.")
    if SAMPLES.exists():
        st.write("Biçimi görmek için örnek dosyalar:")
        for col, name in zip(st.columns(4), ["faturalar.csv", "ekstre.csv", "giderler.csv", "cekler.csv"]):
            col.download_button(name, (SAMPLES / name).read_bytes(), name)
        st.caption((SAMPLES / "OKU.txt").read_text(encoding="utf-8"))
    st.stop()
else:
    res = run_own(store.rev, str(as_of), include_projected)
    res_key = ("own", store.rev, str(as_of), include_projected)

sim, m = res["sim"], res["metrics"]


def record(invoice_id, kind, value=""):
    """Olayı panelde seçili tarihe yazar; bugünse saatiyle birlikte."""
    day = pd.Timestamp(as_of)
    now = pd.Timestamp.now()
    store.add_event(invoice_id, kind, value, now if day.date() == now.date() else day + pd.Timedelta(hours=12))
    st.rerun()


for note in res["notes"]:
    st.caption("• " + note)
if res["disputed_total"]:
    st.caption(f"• İtirazlı {res['disputed_total']:,.0f} TL alacak tahmine ve hatırlatma listesine dahil edilmedi.")
if m["over_60_terms"]:
    st.caption(f"• {m['over_60_terms']} açık faturada vade 60 günden uzun. TTK m.1530'a göre alacaklı KOBİ ise ya da "
               "borçlu büyük işletmeyse vade 60 günü aşamaz; bu sözleşmeleri gözden geçirin.")
if res["simple_model"]:
    st.info(f"Vadesi dolmuş {res['n_train']} fatura bulundu. Bu kadar veriyle öğrenen model yerine "
            "müşteri alışkanlığına dayalı basit tahmin kullanılıyor; bant daha geniş ve daha az kişisel olur.")
if not res["has_outflows"]:
    st.warning("Gider planı yüklenmedi: grafik yalnızca tahsilatları gösteriyor, kasa açığı hesaplanamaz.")

c = st.columns(5)
c[0].metric("Kasa", f"{res['opening']:,.0f} TL")
c[1].metric("Açık alacak", f"{m['open_ar']:,.0f} TL")
c[2].metric("Vadesi geçmiş", f"{m['overdue_ar']:,.0f} TL")
c[3].metric("DSO", f"{m['dso']:.0f} gün")
c[4].metric("90 günde eksiye düşme olasılığı", f"%{sim.prob_any_breach * 100:.0f}")

if sim.breach_day is not None:
    st.warning(f"Kötümser senaryoda kasa {sim.breach_day}. günde ({sim.dates[sim.breach_day]:%d.%m.%Y}) eksiye düşüyor.")
elif res["has_outflows"]:
    st.success("Kötümser senaryoda bile kasa 90 gün boyunca artıda kalıyor.")

fig = go.Figure()
fig.add_scatter(x=sim.dates, y=sim.p90, line=dict(width=0), showlegend=False, hoverinfo="skip")
fig.add_scatter(x=sim.dates, y=sim.p10, fill="tonexty", line=dict(width=0), name="P10–P90 bandı",
                fillcolor="rgba(31,119,180,0.2)")
fig.add_scatter(x=sim.dates, y=sim.p50, name="Beklenen (P50)", line=dict(color="rgb(31,119,180)"))
fig.add_hline(y=0, line_dash="dash", line_color="crimson")
fig.update_layout(height=380, margin=dict(l=0, r=0, t=10, b=0), yaxis_title="Kasa (TL)", hovermode="x unified")
st.plotly_chart(fig, width="stretch")

st.subheader("Açığı kapatmak için ne gerekir?")
gap = run_gap(res_key, res)
if gap["gap"] == 0:
    st.write("Kötümser senaryoda kasa açığı görünmüyor.")
else:
    day = sim.dates[gap["gap_day"]]
    text = f"Kötümser senaryoda en derin açık **{gap['gap']:,.0f} TL** ({day:%d.%m.%Y}). "
    if gap["k"]:
        text += (f"Aşağıdaki listenin ilk **{gap['k']} faturası** ({gap['amount']:,.0f} TL) bir hafta içinde "
                 "tahsil edilirse kötümser senaryoda da kasa artıda kalır.")
    else:
        text += (f"Listedeki öncelikli faturaların tamamı ({gap['amount']:,.0f} TL) tahsil edilse de açık kapanmıyor; "
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
    st.plotly_chart(fig2, width="stretch")
    st.write(f"Senaryoda 90 günde eksiye düşme olasılığı: **%{alt.prob_any_breach * 100:.0f}** "
             f"(bugünkü durumda %{sim.prob_any_breach * 100:.0f}).")

with st.expander("Bu tahmin geçmişte ne kadar tuttu?"):
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
            st.dataframe(bt.rename(columns={
                "origin": "Tahmin tarihi", "actual": "Gerçekleşen (TL)", "p10": "Kötümser (TL)",
                "p50": "Beklenen (TL)", "p90": "İyimser (TL)", "inside": "Bant içinde",
                "err_p50_pct": "Sapma (%)"}).round(0), width="stretch", hide_index=True)

st.subheader("Öncelikli tahsilat listesi")
ranked = res["ranked"]
todo = ranked[ranked["actionable"]].copy()
todo["payday_label"] = todo["payday"].map(actions.payday_label)
todo["stage_label"] = todo["stage"].map(STAGES)
st.dataframe(
    todo[["invoice_id", "customer_name", "due_date", "open_amount", "days_overdue", "p_late", "stage_label",
          "payday_label", "contact_date"]].rename(columns={
        "invoice_id": "Fatura", "customer_name": "Müşteri", "due_date": "Vade", "open_amount": "Tutar (TL)",
        "days_overdue": "Gecikme (gün)", "p_late": "Açık gününe kadar gelmeme olasılığı", "stage_label": "Aşama",
        "payday_label": "Müşterinin ödeme günü", "contact_date": "Önerilen iletişim tarihi"}),
    width="stretch", hide_index=True)

doubtful = ranked[ranked["stage"] == "supheli"]
if len(doubtful):
    with st.expander(f"Şüpheli alacaklar: {len(doubtful)} fatura, {doubtful['open_amount'].sum():,.0f} TL"):
        st.write(f"Bu faturalar {actions.DOUBTFUL_MIN_OVERDUE} günden fazla gecikmiş ve geçmiş verinize göre önümüzdeki "
                 f"90 günde tahsil edilme olasılıkları %{actions.DOUBTFUL_MAX_COLLECT_PROB * 100:.0f}'in altında. "
                 "Hatırlatma listesinde gösterilmezler; yeni bir hatırlatma yerine hukuki yolları değerlendirin.")
        st.dataframe(doubtful[["invoice_id", "customer_name", "due_date", "open_amount", "days_overdue", "p_collect"]]
                     .rename(columns={"invoice_id": "Fatura", "customer_name": "Müşteri", "due_date": "Vade",
                                      "open_amount": "Tutar (TL)", "days_overdue": "Gecikme (gün)",
                                      "p_collect": "90 günde tahsil olasılığı"}), width="stretch", hide_index=True)

st.subheader("Mesaj taslağı")
if len(todo):
    by_id = todo.set_index("invoice_id", drop=False)
    pick = st.selectbox("Fatura", todo["invoice_id"], format_func=lambda i: f"{i} · {by_id.at[i, 'customer_name']}")
    draft = actions.draft_message(by_id.loc[pick], seller)
    body = st.text_area("Taslak (düzenleyebilirsiniz)", draft["body"], height=140, key=f"draft_{pick}")
    if draft["note"]:
        st.info(draft["note"])
    if own:
        st.caption("Mesajı kendi e-posta ya da WhatsApp hesabınızdan gönderdikten sonra aşağıdan kayda geçirin. "
                   f"Kayda geçen fatura {actions.CONTACT_COOLDOWN_DAYS} gün boyunca listede yeniden önerilmez.")
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
            st.dataframe(held[["invoice_id", "customer_name", "open_amount", "disputed", "promised_date"]].rename(columns={
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
            st.dataframe(waiting[["invoice_id", "customer_name", "open_amount", "last_contact"]].rename(columns={
                "invoice_id": "Fatura", "customer_name": "Müşteri", "open_amount": "Tutar (TL)",
                "last_contact": "Son iletişim"}), width="stretch", hide_index=True)
        if not len(held) and not len(waiting):
            st.write("Beklemede fatura yok.")
