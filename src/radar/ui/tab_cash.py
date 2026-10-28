""""Kasa tahmini" sekmesi: kasa bandı, 13 haftalık plan, nakit takvimi ve senaryolar."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from radar import pilot, pipeline
from radar.ui.data import run_customer_delay, run_fx_shift, run_gap, run_scenario
from radar.ui.fmt import show_table, tl, turkish_axes


def render(res, res_key):
    sim, scope = res["sim"], res.get("scope")
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
                   + ", ".join(pilot.SCOPE_NAMES[k] for k, v in scope.items() if not v) + ".")
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
        show_table(exposure.rename(columns={"currency": "Para birimi", "receivable": "Açık dövizli alacak (TL)",
                                            "payable": "Ufuktaki dövizli borç (TL)", "net": "Net (TL)"}),
                   width="stretch", hide_index=True)
        if (exposure["net"] < 0).any():
            st.caption("Net eksi olan dövizde borcunuz alacağınızdan fazla: TL değer kaybederse kasa daralır.")
        fx_info = res["info"]
        if fx_info.get("fx_currencies"):
            st.caption("Kasa bandı kur dalgalanmasını zaten içeriyor (geçmiş kur hareketlerinden, kasanız aleyhine olan "
                       "tarafı esas alarak; ayrıntı \"Tahmin doğruluğu\" sekmesinde). Aşağıdaki kaydırıcı bunun üstüne "
                       "kendi senaryonuzu ekler.")
        if fx_info.get("fx_unknown"):
            st.warning(f"{', '.join(fx_info['fx_unknown'])} için kur geçmişi yok: bu alacaklar girilen kurla sabit sayıldı, "
                       "kur düşüşü kötümser çizgiye girmedi. Karar verirken bu tutarları kur riski açısından ayrıca düşünün.")
        pct = st.slider("TL'nin dövizlere karşı değişimi (%)", -30, 50, 10, step=5,
                        help="Artı: TL değer kaybeder; dövizli alacağın da dövizli borcun da TL karşılığı artar. "
                             "Kur tahmini değildir; kendi senaryonuzu girersiniz.")
        if pct:
            fxs = run_fx_shift(res_key, res, pct / 100)
            st.write(f"Kur %{pct:+d} değişirse: 90 günde eksiye düşme olasılığı **%{fxs['prob_any_breach'] * 100:.0f}** "
                     f"(bugün %{sim.prob_any_breach * 100:.0f}); kötümser en düşük kasa **{tl(fxs['p10_min'])}** "
                     f"(bugün {tl(fxs['p10_min_before'])}).")
