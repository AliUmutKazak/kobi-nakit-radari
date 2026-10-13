"""Yönetici paneli: streamlit run app.py"""
import io
import sys
from pathlib import Path

sys.path.insert(0, "src")

import pandas as pd  # noqa: E402
import plotly.graph_objects as go  # noqa: E402
import streamlit as st  # noqa: E402

from radar import actions, ingest, pipeline  # noqa: E402
from radar.reconcile import reconcile  # noqa: E402

SAMPLES = Path(__file__).parent / "ornekler"
KEEP = ("sim", "ranked", "metrics", "opening", "gap_day", "simple_model", "n_train", "disputed_total", "obs", "as_of")

st.set_page_config(page_title="KOBİ Nakit Akışı Radarı", layout="wide")
st.title("KOBİ Nakit Akışı Radarı")
st.caption("Mesajlar taslaktır; onaylamadan hiçbir şey gönderilmez.")


def _file(upload):
    """Yüklenen dosyayı önbelleğe uygun (ad, içerik) çiftine çevirir."""
    return (upload.name, upload.getvalue()) if upload else None


def _open(pair):
    buf = io.BytesIO(pair[1])
    buf.name = pair[0]
    return buf


@st.cache_data(show_spinner="Simülasyon çalışıyor...")
def run_demo(seed: int, include_projected: bool):
    res = pipeline.demo(seed=seed, include_projected=include_projected)
    return {k: res[k] for k in KEEP} | {"notes": [], "has_outflows": True}


@st.cache_data(show_spinner="Veriler işleniyor ve simülasyon çalışıyor...")
def run_own(inv, ubl, pay, out, chq, opening, terms, as_of, include_projected):
    notes, frames = [], []
    if inv:
        df, n = ingest.load_invoices(_open(inv), terms)
        frames.append(df)
        notes += n
    if ubl:
        df, n = ingest.load_ubl([_open(u) for u in ubl], terms)
        frames.append(df)
        notes += n
    obs = pd.concat(frames, ignore_index=True).drop_duplicates("invoice_id")
    obs = obs[obs["issue_date"] <= pd.Timestamp(as_of)]
    if pay:
        payments, n = ingest.load_payments(_open(pay))
        notes += n
        payments = payments[payments["date"] <= pd.Timestamp(as_of)]
        obs, alloc, unmatched = reconcile(obs, payments)
        notes.append(f"Ekstre: {len(payments)} tahsilatın {len(payments) - len(unmatched)} tanesi faturalarla eşleşti.")
        if len(unmatched):
            notes.append(f"Eşleşmeyen tahsilat tutarı: {unmatched['amount'].sum():,.0f} TL (müşterisi bulunamayan ya da fazla ödeme).")
    outflows = ingest.load_schedule(_open(out)) if out else pd.DataFrame({"date": [], "amount": []})
    cheques = ingest.load_schedule(_open(chq), "drawer") if chq else None
    res = pipeline.forecast(obs.reset_index(drop=True), as_of, opening, outflows,
                            include_projected=include_projected, cheques=cheques)
    if cheques is not None:
        notes.append(f"Çek/senet portföyü: {len(cheques)} adet, {cheques['amount'].sum():,.0f} TL.")
    return {k: res[k] for k in KEEP} | {"notes": notes, "has_outflows": bool(out)}


@st.cache_data(show_spinner="Geçmiş tarihlerde tahmin üretiliyor...")
def run_backtest(obs, as_of):
    return pipeline.backtest_own(obs, as_of)


with st.sidebar:
    source = st.radio("Veri", ["Demo şirket", "Kendi verim"])
    include_projected = st.toggle("Henüz kesilmemiş satışları dahil et", True)
    seller = st.text_input("Mesajlardaki imza (ticaret unvanı ve MERSİS no)", "Örnek Ticaret A.Ş.")
    if source == "Demo şirket":
        seed = st.number_input("Örnek şirket", 1, 99, 7)
    else:
        as_of = st.date_input("Bugünün tarihi", format="DD.MM.YYYY")
        opening = st.number_input("Kasadaki ve bankadaki toplam (TL)", 0.0, step=10_000.0)
        terms = st.number_input("Vadesi yazmayan faturalar için vade (gün)", 0, 365, 30)
        up_inv = st.file_uploader("Kesilen faturalar (CSV / Excel)", ["csv", "xlsx", "xls"])
        up_ubl = st.file_uploader("e-Fatura XML dosyaları", ["xml"], accept_multiple_files=True)
        up_pay = st.file_uploader("Banka ekstresi (isteğe bağlı)", ["csv", "xlsx", "xls"])
        up_out = st.file_uploader("Planlı giderler (isteğe bağlı)", ["csv", "xlsx", "xls"])
        up_chq = st.file_uploader("Çek / senet portföyü (isteğe bağlı)", ["csv", "xlsx", "xls"])

if source == "Demo şirket":
    res = run_demo(int(seed), include_projected)
elif not (up_inv or up_ubl):
    st.info("Başlamak için soldan fatura listenizi (CSV / Excel) ya da e-fatura XML dosyalarınızı yükleyin. "
            "Fatura listesinde en az şu sütunlar olmalı: Fatura No, Cari Unvan, Fatura Tarihi, Tutar. "
            "Vade Tarihi, VKN, Ödeme Tarihi ve Kalan sütunları varsa kullanılır.")
    if SAMPLES.exists():
        st.write("Biçimi görmek için örnek dosyalar:")
        cols = st.columns(4)
        for col, name in zip(cols, ["faturalar.csv", "ekstre.csv", "giderler.csv", "cekler.csv"]):
            col.download_button(name, (SAMPLES / name).read_bytes(), name)
        st.caption((SAMPLES / "OKU.txt").read_text(encoding="utf-8"))
    st.stop()
else:
    try:
        res = run_own(_file(up_inv), tuple(_file(u) for u in up_ubl), _file(up_pay), _file(up_out),
                      _file(up_chq), opening, int(terms), str(as_of), include_projected)
    except ValueError as err:
        st.error(str(err))
        st.stop()

sim, m = res["sim"], res["metrics"]

for note in res["notes"]:
    st.caption("• " + note)
if res["simple_model"]:
    st.info(f"Vadesi dolmuş {res['n_train']} fatura bulundu. Bu kadar veriyle öğrenen model yerine "
            "müşteri alışkanlığına dayalı basit tahmin kullanılıyor; bant daha geniş ve daha az kişisel olur.")
if res["disputed_total"]:
    st.caption(f"• İtirazlı {res['disputed_total']:,.0f} TL alacak tahmine ve hatırlatma listesine dahil edilmedi.")
if m["over_60_terms"]:
    st.caption(f"• {m['over_60_terms']} açık faturada vade 60 günden uzun. TTK m.1530'a göre alacaklı KOBİ ise ya da "
               "borçlu büyük işletmeyse vade 60 günü aşamaz; bu sözleşmeleri gözden geçirin.")
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
todo = res["ranked"][res["ranked"]["actionable"]].copy()
todo["payday_label"] = todo["payday"].map(actions.payday_label)
st.dataframe(
    todo[["invoice_id", "customer_name", "due_date", "open_amount", "days_overdue", "p_late", "stage",
          "payday_label", "contact_date"]].rename(columns={
        "invoice_id": "Fatura", "customer_name": "Müşteri", "due_date": "Vade", "open_amount": "Tutar (TL)",
        "days_overdue": "Gecikme (gün)", "p_late": "Açık gününe kadar gelmeme olasılığı", "stage": "Aşama",
        "payday_label": "Müşterinin ödeme günü", "contact_date": "Önerilen iletişim tarihi"}),
    width="stretch", hide_index=True)

st.subheader("Mesaj taslağı")
if len(todo):
    by_id = todo.set_index("invoice_id", drop=False)
    pick = st.selectbox("Fatura", todo["invoice_id"], format_func=lambda i: f"{i} · {by_id.at[i, 'customer_name']}")
    draft = actions.draft_message(by_id.loc[pick], seller)
    st.text_area("Taslak (düzenleyebilirsiniz)", draft["body"], height=140)
    if draft["note"]:
        st.info(draft["note"])
