""""Tahmin doğruluğu" sekmesi: tahminin dayanağı, geri test, Aşama 0, pilot raporu ve kayıtlar."""
import io
import json

import numpy as np
import pandas as pd
import streamlit as st

from radar import anonymize, fx, pilot, standards
from radar.ui.data import retro_data_key, run_backtest, run_pilot, secret_key
from radar.ui.fmt import show_table, verdict_text


def render(res, res_key, store, own):
    info = res["info"]
    st.write("**Bu tahmin neye dayanıyor?**")
    st.write(f"• {info['n_invoices']} fatura, {info['n_customers']} müşteri; geçmiş {info['history_from']:%d.%m.%Y} tarihinden başlıyor.")
    st.write(f"• Ödeme davranışını öğrenmek için vadesi dolmuş {info['n_train']} fatura kullanıldı"
             + (" (az olduğu için basit yöntem: müşterinin geçmiş medyanı)." if info["simple_model"]
                else " (LightGBM kantil regresyonu ile müşterinin geçmiş medyanının birleşimi)."))
    st.write(f"• Tahmin aralığının genişliği, sistemin geçmiş dört çeyrekte {info['n_calibration']} faturada yaptığı "
             "ileriye dönük tahminlerin hatasından ayarlandı."
             + (" Bu sayı az; aralıklar varsayılan değerlere yakın." if info["n_calibration"] < 100 else ""))
    if info.get("sales_method") and info.get("projected_share"):
        st.write(f"• Önümüzdeki 90 günde beklenen tahsilatın %{info['projected_share'] * 100:.0f}'i henüz kesilmemiş "
                 "satışlardan geliyor. Bu kısım satışlar geçmişteki gibi giderse gelir; satışlar düşerse kasa bu kadar dolu "
                 "olmaz. Yalnızca kesinleşmiş kalemlerle görmek için \"Gelecek satışları hesaba kat\" seçeneğini kapatın.")
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
    if info.get("outflow_spread"):
        st.write(f"• Banka geçmişinize göre aylık giderleriniz dalgalanıyor (aylık toplamın ortalamaya oranı, 10 aydan 8'inde "
                 f"±%{info['outflow_spread'] * 50:.0f} aralığında). Bu belirsizlik kasa bandına katıldı; planlanan giderler "
                 "kesin sayılmadı.")
    if info.get("fx_currencies"):
        st.write(f"• Dövizli alacak ve borçlarda ({', '.join(info['fx_currencies'])}) kur belirsizliği kasa bandına "
                 "katıldı: para geldiği ya da ödendiği gün kur bugünkünden farklı olabilir. Dalgalanma, kurların 2005'ten "
                 f"{pd.Timestamp(info['fx_data_end']):%d.%m.%Y} tarihine kadarki geçmişinden alındı. Kur farkının "
                 "kasayı büyüteceğine güvenilmez: alacağınız borcunuzdan fazla olan dövizde TL'nin değer kaybetmeye "
                 "devam edeceği varsayılmadı"
                 + (f"; borcunuz alacağınızdan fazla olan dövizde ({', '.join(info['fx_short'])}) son 3 yılın değer "
                    "kaybı hızının süreceği varsayıldı (kur yükselirse borç büyür)" if info.get("fx_short") else "")
                 + ". " + fx.SOURCE)
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
    retro_json = ""
    if own:
        st.divider()
        st.write("**Aşama 0: geriye dönük pilot testi** (pilot protokolü 1.6). Son bir yılda her hafta için, o gün "
                 "eldeki bilgiyle 14 ve 30 günlük tahsilat tahmin edilir ve gerçekleşenle karşılaştırılır. Ölçütler "
                 "ileriye dönük pilottakilerle aynıdır; sonuç pilotun başında işletmeyle konuşulur.")
        n_retro = pilot.retro_origins(res["obs"], res["as_of"])
        data_key = retro_data_key(store, res)              # ayar değişiklikleri sayılmaz
        saved = json.loads(store.get("retro_meta", "{}"))
        if n_retro < pilot.RETRO_MIN_ORIGINS:
            st.caption(f"Yeterli geçmiş yok: her tahmin gününden önce en az {pilot.RETRO_MIN_TRAIN_DAYS} günlük geçmiş ve "
                       f"en az {pilot.RETRO_MIN_ORIGINS} haftalık tahmin günü gerekir (yaklaşık 8 aylık veri).")
        elif st.button(f"Aşama 0 testini çalıştır ({n_retro} hafta; bilgisayara göre birkaç dakika sürer)"):
            bar = st.progress(0.0, text="Geçmiş haftalar tek tek tahmin ediliyor...")
            retro = pilot.retrospective(res["obs"], res["as_of"], events=res.get("events"),
                                        progress=lambda f: bar.progress(f, text=f"Geçmiş haftalar: %{f * 100:.0f}"))
            bar.empty()
            store.set("retro_result", retro.to_json(orient="records", force_ascii=False))
            saved = {"data": data_key, "n": n_retro, "ran": f"{pd.Timestamp.now():%d.%m.%Y %H:%M}"}
            store.set("retro_meta", json.dumps(saved))
            store.audit("Aşama 0 geri testi", f"{n_retro} hafta")
            # B1 kabul marjı (protokol 1.7): ilk ileriye dönük kayıt alınana kadar son Aşama 0'dan; sonra dondurulur.
            if not len(store.pilot_records()) and "b1_m2" in retro:
                store.set("b1_margins", json.dumps({
                    "m2": {str(int(r["ufuk_gun"])): r["b1_m2"] for _, r in retro.iterrows() if pd.notna(r.get("b1_m2"))},
                    "m1": {str(int(r["ufuk_gun"])): r["b1_m1"] for _, r in retro.iterrows() if pd.notna(r.get("b1_m1"))},
                    "tarih": saved["ran"]}))
        if saved and store.get("retro_result", ""):
            retro = pd.read_json(io.StringIO(store.get("retro_result")), orient="records")
            if saved.get("data") != data_key:
                st.caption(f"Son Aşama 0 testi {saved.get('ran')} tarihinde, o günkü verilerle yapıldı. Veriler değiştiyse "
                           "yeniden çalıştırın.")
            frozen = json.loads(store.get("b1_margins", "{}"))
            if frozen:
                m2 = frozen.get("m2", {})
                st.caption("B1 kabul marjı (protokol 1.7; FDA 2016 eşdeğerlik yaklaşımı): "
                           + ("; ".join(f"{h} gün {float(v):.1f} puan" for h, v in m2.items()) if m2 else
                              "belirlenemedi (en iyi basit yöntem \"vadesinde öder\"den anlamlı biçimde iyi çıkmadı; "
                              "B1 yalnızca model üstün çıkarsa geçer)")
                           + f". Hesap tarihi {frozen.get('tarih')}; "
                           + ("ilk ileriye dönük kayıt alındığı için dondurulmuştur." if len(store.pilot_records())
                              else "ilk ileriye dönük kayıt alınınca dondurulur."))
            show_table(retro.assign(**{c: retro[c].map(verdict_text) for c in ("B1", "B2") if c in retro}).rename(columns={
                "ufuk_gun": "Ufuk (gün)", "tahmin_tarihi_sayisi": "Tahmin günü", "sapma_model_%": "Model (%)",
                "sapma_medyan_%": "Müşteri medyanı (%)", "sapma_vade_%": "Vadesinde öder (%)",
                "sapma_oran_%": "Tahsilat oranı (%)", "bant_ici": "Bant içinde", "bant_genisligi_%": "Bant genişliği (%)",
                "aralik_skoru_%": "Aralık skoru (%)", "dm_sonuc": "İsabet testi (Diebold-Mariano)",
                "dm_kiyas": "Kıyaslanan yöntem", "alt_asim": "Kötümserin altı (adet)", "ust_asim": "İyimserin üstü (adet)",
                "basel_alt": "Basel bölgesi (alt uç)", "kupiec_p": "Kupiec p değeri", "B1": "Diebold-Mariano: geride değil",
                "B2": "B2 (aralık)", "b1_m1": "Kontrol etkisi M1 (puan)", "b1_m2": "B1 marjı M2 (puan)",
                "b1_kontrol": "Kontrol yöntemi"}), width="stretch", hide_index=True)
            st.caption("Haftalık tahmin günlerinin ufukları üst üste biner; isabet testi bunu hesaba katar. Geriye dönük "
                       "test geçmiş kayıtlara sonradan bakar (ör. sonradan düzeltilen kayıtlar); bu yüzden ileriye dönük "
                       "pilotun kararının yerine geçmez. Model bir ufukta \"geride\" çıkarsa, protokole göre o işletmede "
                       "ileriye dönük dönemde en iyi basit yöntem esas alınır.")
            retro_json = store.get("retro_result")
    st.divider()
    st.write("**Pilot raporu.** Tek sayfalık, yazdırılabilir özet: kasa bandı, 13 haftalık plan, öncelikli tahsilat ve "
             "tahminin bu işletmenin geçmişinde basit yöntemlere karşı ne kadar tuttuğu (Aşama 0 yapıldıysa onun sonucu).")
    hide = st.checkbox("Müşteri ve işletme adlarını gizle (rapor paylaşılacaksa)", True)
    if st.button("Pilot raporunu hazırla"):
        seller_name = (store.get("seller", "") if own else "Demo şirket") or "İşletme"
        label = anonymize.firm_alias(secret_key(store), seller_name) if hide and own else seller_name
        page = run_pilot(res_key, res, label, hide, retro_json, str(store.path))
        store.audit("pilot raporu hazırlandı", "adlar gizli" if hide else "adlar açık")
        st.download_button("Raporu indir (HTML; tarayıcıda açıp yazdırabilirsiniz)", page,
                           f"pilot_raporu_{pd.Timestamp(res['as_of']):%Y%m%d}.html", "text/html")
    records = store.pilot_records() if own else pd.DataFrame()
    if len(records):
        with st.expander(f"Pilot kayıtları: {records['as_of'].nunique()} hafta"):
            reason = pilot.record_due(records, res["as_of"], res.get("last_activity"))
            if reason:
                st.caption(reason)
            frozen_m2 = {int(h): float(v) for h, v in json.loads(store.get("b1_margins", "{}")).get("m2", {}).items()}
            detail, summary = pilot.score(pilot.records_from_table(records), res["obs"], events=res.get("events"),
                                          margins=frozen_m2)
            parts = pilot.component_variance(records, res["obs"], res.get("events"), store.load("bank_outflows"))
            if len(parts):
                st.write("Kasa kayıtlarında kalem bazında beklenen ve gerçekleşen (AFP önerisi: kasa ıskaladığında hatanın "
                         "hangi kalemden geldiğini gösterir). Giderlerin gerçekleşeni banka ekstresindeki çıkışlardır.")
                show_table(parts.rename(columns={"hafta": "Kayıt haftası", "ufuk": "Ufuk (gün)", "kalem": "Kalem",
                                                 "beklenen": "Beklenen (TL)", "gerceklesen": "Gerçekleşen (TL)",
                                                 "fark": "Fark (TL)"}), width="stretch", hide_index=True)
            if len(summary):
                st.write("Süresi dolan kayıtlarda tahmin ile gerçekleşen (sapma ve aralık skoru: düşük iyi). "
                         "Tahsilat: açık faturalardan gelen para, kısmi ödemeler dahil. Kasa: o gün girdiğiniz "
                         "kasa ve banka toplamı.")
                view = summary.assign(
                    hedef=summary["hedef"].map({"tahsilat": "Tahsilat", "kasa": "Kapanış kasası"}),
                    fark_guven_araligi=summary["fark_guven_araligi_95"].map(
                        lambda v: f"{v[0]:+.1f} / {v[1]:+.1f} puan" if isinstance(v, tuple) else "az kayıt"),
                    **{c: summary[c].map(verdict_text) for c in ("B1", "B2") if c in summary})
                show_table(view.rename(columns={
                    "hedef": "Hedef", "ufuk_gun": "Ufuk (gün)", "kayit": "Kayıt", "uyarili_kayit": "Uyarılı (dışarıda)",
                    "sapma_model_%": "Model (%)", "sapma_medyan_%": "Müşteri medyanı (%)",
                    "sapma_oran_%": "Tahsilat oranı (%)", "sapma_vade_%": "Vadesinde öder (%)",
                    "sapma_sabit_%": "Kasa değişmez (%)", "bant_ici": "Bant içinde",
                    "bant_genisligi_%": "Bant genişliği (%)", "aralik_skoru_%": "Aralık skoru (%)",
                    "fark_guven_araligi": "Model eksi en iyi basit yöntem, %95 aralık", "B1_marj": "B1 marjı (puan)",
                    "B1_sonuc": "B1 sonucu",
                    "dm_sonuc": "İsabet testi (Diebold-Mariano)", "alt_asim": "Kötümserin altı (adet)",
                    "ust_asim": "İyimserin üstü (adet)", "basel_alt": "Basel bölgesi (alt uç)",
                    "kupiec_p": "Kupiec p değeri", "B1": "B1, bu işletme (betimleyici)", "B2": "B2 (aralık)",
                    "fark_tahmin": "Fark tahmini (puan)", "fark_se": "Farkın standart hatası",
                    "ortusmeyen_kayit": "Örtüşmeyen kayıt", "ortusmeyen_alt_asim": "Örtüşmeyen: kötümserin altı",
                    "ortusmeyen_ust_asim": "Örtüşmeyen: iyimserin üstü",
                    "ortusmeyen_kupiec_p": "Örtüşmeyen: Kupiec p"}).drop(
                    columns=["eksik_hafta", "kasa_guncel_olmayan_kayit", "fark_guven_araligi_95"], errors="ignore"),
                    width="stretch", hide_index=True)
                gaps, stale = int(summary["eksik_hafta"].iloc[0]), int(summary["kasa_guncel_olmayan_kayit"].iloc[0])
                if gaps or stale:
                    st.warning(f"Kayıt alınmayan hafta: {gaps}. Kasa tutarı o gün güncellenmemiş kayıt: {stale} (bunlar "
                               "kapanış kasası ölçümüne girmez). Eksik haftalar sonuçların dayandığı kayıt sayısını azaltır; "
                               "her hafta bir kez açıp güncel dosyaları yüklemek yeterlidir.")
                st.caption("Ölçütler uluslararası standartlardır, kendi eşiğimiz yoktur. B1 (protokol 1.7): model eksi en "
                           "iyi basit yöntem sapma farkının %95 güven aralığının üst sınırı, Aşama 0'dan dondurulan "
                           "marjın altındaysa \"eşdeğer\", sıfırın altındaysa \"üstün\"; değilse \"kanıtlanamadı\" "
                           "(FDA 2016 eşdeğerlik yaklaşımı). Pilotun kararı bu işletmenin sonucuyla değil, bütün pilot işletmelerinin "
                           "birleşik analiziyle verilir (protokol 1.8); buradaki B1 betimleyicidir. Diebold-Mariano sonucu ayrıca gösterilir. B2: kötümser uç için Basel Komitesi trafik ışığı (BIS 1996) yeşil ve Kupiec "
                           "(1995) kapsama testleri reddetmiyorsa geçer. Haftalık kayıtların ufukları üst üste biner: "
                           "isabet testi ve güven aralığı bunu hesaba katar, Basel ve Kupiec katmaz (Christoffersen "
                           "1998). Bu yüzden aşımlar örtüşmeyen alt örneklemle (her ufuk süresinde bir kayıt) de verilir.")
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
