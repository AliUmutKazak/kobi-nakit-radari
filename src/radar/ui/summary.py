"""Tahminin üstündeki özet: uyarılar, mali müşavir görünümü, göstergeler ve veri notları."""
import hashlib
import io
import json

import pandas as pd
import streamlit as st

from radar import benchmark, fx, ingest, pilot, pipeline
from radar.ui.data import get_store, retro_data_key
from radar.ui.fmt import HIGH_RISK, SCOPE_NAMES, show_table, tl, tr_number


def render(res, store, own, businesses):
    sim, m = res["sim"], res["metrics"]
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
            weekly = pd.concat([pilot.forward_record(res["obs"], res["as_of"], events=res.get("events"),
                                                     payments_through=res["info"].get("payments_through")),
                                pilot.cash_record(res)], ignore_index=True)
        digest = hashlib.sha256("|".join(store.get(f"hash_{n}", "") for n in
                                         ("invoices", "payments", "outflows", "payables", "cheques")).encode()).hexdigest()
        meta = {"surum": pilot.VERSION, "kesim": f"{pd.Timestamp(res['as_of']):%Y-%m-%d}",
                "son_hareket": f"{res['last_activity']:%Y-%m-%d}", "veri_ozeti": digest[:16],
                "yontem": "müşteri medyanı (basit)" if res["simple_model"] else "LightGBM + müşteri medyanı birleşimi",
                "eslesme_orani": res.get("match_rate"), "kapsam": res.get("scope", {}),
                "acilis_guncel": store.get("opening_date") == f"{pd.Timestamp(res['as_of']):%Y-%m-%d}",
                "cevrimici_ayar": res["ctx"]["calib"].get("online"), "genisletme": res["info"].get("widen"),
                "bilesenler": pilot.cash_components(res)}
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
    if own:
        # Tahmin girilen kasa tutarından başlar; eski bir tutar bütün çizgiyi aynı miktarda kaydırır.
        opened, as_of_day = store.get("opening_date", ""), pd.Timestamp(res["as_of"]).normalize()
        bank_day = store.get("bank_balance_date", "")
        if not opened:
            st.warning("Kasa ve banka tutarının hangi gün girildiği kayıtlı değil. Tahmin bu tutardan başlıyor; bugünkü "
                       "toplamı \"Temel bilgiler\" bölümünde kontrol edin.")
        elif bank_day and pd.Timestamp(bank_day) > pd.Timestamp(opened):
            st.warning(f"Banka ekstresi ({pd.Timestamp(bank_day):%d.%m.%Y}) kasa tutarından daha yeni: kasa tutarı en son "
                       f"{pd.Timestamp(opened):%d.%m.%Y} tarihinde değiştirildi. Tutar güncel değilse tahminin tamamı o "
                       "fark kadar kayar; \"Temel bilgiler\" bölümünde güncelleyin.")
        elif pd.Timestamp(opened) < as_of_day:
            st.info(f"Kasa tutarı en son {pd.Timestamp(opened):%d.%m.%Y} tarihinde değiştirildi; tahmin "
                    f"{as_of_day:%d.%m.%Y} günü bu tutarla başlıyor. Bugünkü toplam farklıysa güncelleyin.")

    if own and len(businesses) > 1:
        with st.expander(f"Mali müşavir görünümü: bu bilgisayardaki {len(businesses)} işletme, kasa riskine göre"):
            rows = []
            for name, path in businesses.items():
                saved = json.loads(get_store(str(path)).get("portfolio_summary", "{}"))
                o = saved.get("ozet")
                rows.append({"İşletme": name, **({
                    "Eksiye düşme riski": o["risk"], "Kötümser en düşük kasa (TL)": o["p10_min"],
                    "Kötümserde eksiye düştüğü gün": pd.Timestamp(o["breach_date"]).strftime("%d.%m.%Y") if o["breach_date"] else "–",
                    "Güvenle harcanabilir (TL)": o["safe"], "Vadesi geçmiş alacak (TL)": o["overdue_ar"],
                    "Tahmin tarihi": pd.Timestamp(o["as_of"]).strftime("%d.%m.%Y"), "Son hesap": saved.get("hesap", "")}
                    if o else {"Eksiye düşme riski": float("nan"), "Son hesap": "henüz hesaplanmadı"})})
            table = pd.DataFrame(rows).sort_values("Eksiye düşme riski", ascending=False, na_position="last")
            # Metin olarak gösterilir ("en az %X"); sütun adında "risk" geçerse show_table sayıya çevirip boşaltıyordu.
            table.insert(1, "90 günde eksiye düşme", table.pop("Eksiye düşme riski").map(
                lambda v: "–" if v != v else (f"en az %{v * 100:.0f}" if v >= HIGH_RISK else f"%{v * 100:.0f}")))
            show_table(table, width="stretch", hide_index=True)
            st.caption("Her satır, o işletme panelde en son açıldığında hesaplanan özettir; güncel görmek için işletmeyi "
                       "seçip açın. Yalnızca bu bilgisayarda kayıtlı işletmeler gösterilir ve hiçbir veri başka yere "
                       "gönderilmez. Tabloda müşteri adı ya da fatura bilgisi yoktur. Her işletme için işletmeyle yapılan "
                       "sözleşme ve mali müşavirin sır saklama yükümlülüğü (3568 sayılı Kanun) geçerlidir.")

    # İki satır üçer gösterge: tek satırda altı gösterge dizüstü genişliğinde (1366 piksel) tutarları kesiyordu.
    # Üst satır karar sayıları (kasa, güvenle harcanabilir, risk), alt satır alacak durumu.
    top, bottom = st.columns(3), st.columns(3)
    c = [top[0], bottom[0], bottom[1], bottom[2], top[2], top[1]]
    c[0].metric("Kasa ve banka", tl(res["opening"], compact=True), help="Bugün kasada ve bankada olan toplam para.")
    c[5].metric("Güvenle harcanabilir", tl(pipeline.safe_to_spend(sim), compact=True),
                help="Bugün bundan fazlasını plan dışı harcarsanız, önümüzdeki 90 günde kasanın en az bir gün eksiye düşmesi "
                     "10 benzer durumun 1'inden sıktır. Kötümser senaryodan hesaplanır: kasayı olduğundan dolu göstermek, "
                     "biraz eksik göstermekten daha pahalıdır. Yeni satışlar hesaba katılıyorsa onların gelmeme riski de dahildir.")
    c[1].metric("Açık alacak", tl(m["open_ar"], compact=True), help="Müşterilerin henüz ödemediği faturaların toplamı.")
    c[2].metric("Vadesi geçmiş", tl(m["overdue_ar"], compact=True), help="Açık alacağın vadesi dolmuş kısmı.")
    c[3].metric("Ortalama tahsil süresi", f"{m['dso']:.0f} gün",
                help="Alacaklarınız ortalama kaç günlük satışa denk geliyor (DSO). Düşük olması iyidir.")
    risk_pct = f"%{sim.prob_any_breach * 100:.0f}"
    c[4].metric("Eksiye düşme riski", f"en az {risk_pct}" if sim.prob_any_breach >= HIGH_RISK else risk_pct,
                help="Önümüzdeki 90 gün içinde kasanın en az bir gün eksiye düşme olasılığı. Bağımsız doğrulamada bu "
                     "olasılıklar ortaya doğru sıkışık çıktı (Spiegelhalter testi): yüksek riskte gerçek risk gösterilenden "
                     "yüksek, düşük riskte düşük. Bu yüzden %50 ve üzerindeki değerler \"en az\" diye gösterilir. "
                     "Karar için kötümser çizgiyi esas alın.")
    # Frekans biçimi (Spiegelhalter, Pearson ve Short 2011, Science 333): sabit paydalı sayı ve iki sonuç birlikte.
    _bad = int(round(sim.prob_any_breach * 100))
    _high = sim.prob_any_breach >= HIGH_RISK
    st.caption(f"100 olası senaryo: {'en az ' if _high else ''}{_bad} senaryoda kasa önümüzdeki 90 günde en az bir gün eksiye "
               f"düşüyor, {'en çok ' if _high else ''}{100 - _bad} senaryoda düşmüyor.")
    if own and store.get("sector"):
        line = benchmark.compare(m["dso"], store.get("sector"), store.get("size", "kucuk"))
        if line:
            st.info(line + " Tanımlar yakın ama aynı değil: TCMB oranı yıllık ortalama alacağa, buradaki süre bugünkü "
                    "açık alacağa dayanır.")
    shortfall = pipeline.expected_shortfall(sim)
    if shortfall < 0:
        st.warning(f"Kötü durumda ortalama açık: en kötü 10 senaryonun ortalamasında kasa en derin noktasında "
                   f"{tl(-shortfall)} eksiye düşüyor. Eksiye düşme olasılığı açığın derinliğini göstermez; bu tutar, "
                   "hazır tutulması gereken ek kaynak (kredi limiti, erteleme, erken tahsilat) için bir ölçüdür.")
    if sim.prob_any_breach >= HIGH_RISK:
        st.error(f"Eksiye düşme riski yüksek (en az %{sim.prob_any_breach * 100:.0f}). Bağımsız doğrulamada %80 gösterilen "
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
    if own and store.get("retro_result", "") and json.loads(store.get("retro_meta", "{}")).get("data") == retro_data_key(store, res):
        _retro = pd.read_json(io.StringIO(store.get("retro_result")), orient="records")
        for rep in pilot.simple_replacements(_retro, res["obs"], res["as_of"]):
            st.warning(f"**{rep['ufuk_gun']} günlük tahsilat için bu işletmede basit yöntem esas alınır.** Aşama 0 geriye "
                       f"dönük testinde model, \"{rep['ad']}\" yönteminin istatistiksel olarak gerisinde kaldı "
                       f"(Diebold-Mariano, %5; geçmiş sapma model %{rep['sapma_model']:.0f}, bu yöntem "
                       f"%{rep['sapma_yontem']:.0f}). Bu yönteme göre önümüzdeki {rep['ufuk_gun']} günde açık faturalardan "
                       f"beklenen tahsilat: **{tl(rep['tutar'])}**. Basit yöntemin belirsizlik bandı yoktur; kasa grafiği ve "
                       "güvenle harcanabilir tutar modelden gelir, bu ufukta onlara temkinli yaklaşın.")
    for note in notes:
        if note.startswith("DİKKAT"):           # kasayı olduğundan dolu gösterebilecek veri sorunları gizlenmez
            st.warning(note)
    if own:
        for cur, given, ref, diff in fx.stale_rates(ingest.parse_rates(store.get("rates", ""))):
            st.warning(f"Girdiğiniz {cur} kuru ({tr_number(given, 2)}) ECB'nin {fx.latest()[0]:%d.%m.%Y} kurundan "
                       f"({tr_number(ref, 2)}) %{abs(diff) * 100:.0f} {'düşük' if diff < 0 else 'yüksek'}; bu fark, son 3 yılda "
                       "kurun bir ayda gösterdiği olağan hareketten büyük. Kur eskiyse dövizli tutarlar yanlış çevrilir. "
                       "\"Diğer ayarlar\" bölümünde güncelleyin ve dövizli tutar içeren dosyaları yeniden yükleyin (kayıtlı "
                       "dosyalar yüklendikleri günkü kurla çevrilmiş olarak saklanır).")
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
