"""Yönetici paneli: streamlit run app.py"""
import json
import sys
from pathlib import Path

sys.path.insert(0, "src")

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from radar import access, anonymize, benchmark, fx, ingest, mailer, pipeline  # noqa: E402
from radar.store import encrypt_backup, list_businesses, synced_folder  # noqa: E402
from radar.ui import summary as overview, tab_accuracy, tab_cash, tab_collect  # noqa: E402
from radar.ui.data import (MAPPABLE, add_business, add_sample_business, anonymous_package,  # noqa: E402
                           get_store, open_upload, parse_bank, parse_invoices, run_demo, run_own, save_upload)
from radar.ui.fmt import synced_state, tl, tr_number  # noqa: E402

ROOT = Path(__file__).parent
SAMPLES = ROOT / "ornekler"

st.set_page_config(page_title="KOBİ Nakit Akışı Radarı", layout="wide")
st.title("KOBİ Nakit Akışı Radarı")
st.caption("Mesajlar taslaktır; bu panel hiçbir mesajı kendiliğinden göndermez. "
           "Nasıl kullanılacağı: programla birlikte gelen KULLANIM_KILAVUZU.md dosyası.")


BUSINESSES = list_businesses()
# Seçili işletme, seçim kutusundan ayrı tutulur: kutu demo modunda çizilmediğinde seçim kaybolmasın.
if st.session_state.get("active_business") not in BUSINESSES:
    st.session_state["active_business"] = next(iter(BUSINESSES))
store = get_store(str(BUSINESSES[st.session_state["active_business"]]))
_synced = synced_folder(store.path)
if _synced:
    st.error(f"Veriler bulutla eşitlenen bir klasörde ({_synced}): {store.path}. Müşteri bilgileri buluta kopyalanır. "
             "Programı RADAR_DB ayarı olmadan açın ya da verileri eşitlenmeyen bir klasöre taşıyın (KULLANIM_KILAVUZU).")

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
            opening_key = f"opening::{store.path}"
            synced_state(opening_key, float(store.get("opening", 0)))
            opening = st.number_input("Kasa ve bankadaki toplam para (TL)", 0.0, key=opening_key, step=10_000.0,
                                      help="Her kullanımda güncelleyin; tahmin bu tutardan başlar. Yalnızca gerçekten "
                                           "elinizde olan para: kredili mevduat (KMH), kredi kartı ya da kredi limiti, "
                                           "blokeli tutarlar ve henüz tahsil edilmemiş çekler dahil değildir. Limiti "
                                           "bakiye gibi yazmak kasayı olduğundan dolu gösterir.")
            if store.get("bank_balance", ""):
                st.caption(f"Yüklenen banka ekstresinde son bakiye: {tl(float(store.get('bank_balance')))} "
                           f"({pd.Timestamp(store.get('bank_balance_date')):%d.%m.%Y}). Kasadaki nakit ve başka "
                           "bankalardaki hesaplar bu tutara dahil değildir.")
                if float(store.get("bank_balance")) >= 0:
                    def use_bank_balance(key=opening_key, value=float(store.get("bank_balance"))):
                        st.session_state[key] = value

                    st.button("Ekstre bakiyesini kasa tutarına yaz", on_click=use_bank_balance,
                              help="Tek banka hesabınız varsa ve kasada nakit yoksa her hafta elle girmek yerine bunu "
                                   "kullanın. Başka hesaplarınız varsa onları ekleyin.")
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
            auto_unplanned = st.checkbox("Plan dışı ödemeleri banka geçmişinden ekle", store.get("auto_unplanned", "1") == "1",
                                         help="Banka ekstresi yüklüyse son 90 günün gerçek çıkışları planladığınız giderlerle "
                                              "karşılaştırılır; plan geçmişin altındaysa fark tahmini gider olarak eklenir "
                                              "(ihtiyatlılık: giderler olduğundan düşük gösterilmez).")
            store.set("auto_unplanned", "1" if auto_unplanned else "0")
            match_tol = st.number_input(
                "Banka eşleştirme toleransı (TL)", 0.0, 1000.0, float(store.get("match_tol", 0.01)), step=1.0,
                help="Gelen para ile fatura tutarı arasında kabul edilen fark (ör. havale masrafı). Yükseltirseniz "
                     "daha çok eşleşme olur, ama yanlış eşleşme riski de artar.")
            store.set("match_tol", match_tol)
            terms = st.number_input("Vadesi yazmayan faturalar için vade (gün)", 0, 365, int(store.get("terms", 30)),
                                    help="TTK m.1530: vade yazmıyorsa borçlu, faturayı aldıktan 30 gün sonra temerrüde düşer.")
            rates_key = f"rates_text::{store.path}"            # işletme değişince kendi kurları gelsin
            synced_state(rates_key, store.get("rates", ""))
            rates_text = st.text_input("Döviz kurları (dövizli fatura, çek, borç ya da gider varsa)", key=rates_key,
                                       placeholder="USD=49,50; EUR=55,60",
                                       help="Dövizli tutarlar bu kurla TL'ye çevrilir. Kuru girilmeyen dövizli alacak ve çek "
                                            "tahmine katılmaz; kuru girilmeyen dövizli borç ve gider TL sayılır ve uyarılır.")
            ecb = fx.latest()
            if ecb:
                ecb_day, ecb_rates = ecb
                st.caption(f"Avrupa Merkez Bankası (ECB) referans kurları, {ecb_day:%d.%m.%Y}: "
                           + "; ".join(f"{c} = {tr_number(v, 4)}" for c, v in ecb_rates.items())
                           + ". Bilgi amaçlıdır: bankanızın ve TCMB'nin kuru farklı olabilir; vergi ve muhasebe "
                             "değerlemesinde ECB kuru kullanılmaz. Veriler ECB internet sitesinden ücretsiz edinilebilir.")

                def use_ecb_rates(key=rates_key, rates=ecb_rates):
                    st.session_state[key] = "; ".join(f"{c}={v:.4f}".replace(".", ",") for c, v in rates.items())

                b1, b2 = st.columns(2)
                b2.button("ECB kurlarını alana yaz", on_click=use_ecb_rates,
                          help="Döviz kurları alanına ECB'nin son kurlarını yazar; dilerseniz bankanızın kuruyla değiştirin.")
            else:
                b1 = st
            if b1.button("Kurları ECB'den güncelle (internet)",
                         help="Avrupa Merkez Bankası'nın kur geçmişini indirir (yaklaşık 0,7 MB, ecb.europa.eu). ECB'ye "
                              "işletme verisi gönderilmez; giden tek bilgi indirme isteğidir. İndirilen dosya denetlenir; "
                              "sorun varsa kullanılmaz ve paketteki kurlarla devam edilir."):
                try:
                    day = fx.update_from_ecb()
                    store.audit("ECB kurları güncellendi", f"{day:%Y-%m-%d}")
                    st.success(f"Kurlar güncellendi: son kur günü {day:%d.%m.%Y}.")
                except Exception as err:          # ağ yok, site değişti, dosya denetimden geçmedi
                    st.error(f"Kurlar güncellenemedi ({err}). Paketteki kurlar kullanılmaya devam ediyor.")
            st.caption(f"Verilerin saklandığı dosya: {store.path}")
            undoable = [n for n in ("invoices", "payments", "outflows", "payables", "cheques") if store.can_undo(n)]
            if undoable:
                names = {"invoices": "Satışlar", "payments": "Banka ekstresi", "outflows": "Planlı giderler",
                         "payables": "Ödenecek faturalar", "cheques": "Çek / senet"}
                which = st.selectbox("Son yüklemeyi geri al", undoable, format_func=names.get)
                if st.button("Önceki dosyaya dön"):
                    store.undo(which)
                    if which == "payments" and store.can_undo("bank_outflows"):
                        store.undo("bank_outflows")
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
                    lambda ups: parse_invoices(store, ups, int(terms), ingest.parse_rates(rates_text)))
        save_upload(store, "payments", uploads["payments"], lambda ups: parse_bank(store, ups))
        def parse_outflows(ups):
            out_notes: list[str] = []
            return ingest.load_schedule(open_upload(ups[0]), rates=ingest.parse_rates(rates_text), notes=out_notes), out_notes

        save_upload(store, "outflows", uploads["outflows"], parse_outflows)
        save_upload(store, "payables", uploads["payables"],
                    lambda ups: ingest.load_payables(open_upload(ups[0]), int(terms), ingest.parse_rates(rates_text)))
        save_upload(store, "cheques", uploads["cheques"],
                    lambda ups: ingest.load_cheques(open_upload(ups[0]), ingest.parse_rates(rates_text)))

own = source == "Kendi verim"
for name, (title, fields, required) in MAPPABLE.items():
    upload = st.session_state.get(f"needmap_{name}") if own else None
    if upload is None:
        continue
    st.subheader(f"{title}: sütunları eşleştirin")
    st.write("Dosyadaki başlıklar otomatik tanınamadı. Her alan için dosyanızdaki karşılığını seçin; "
             "seçiminiz kaydedilir ve aynı biçimdeki sonraki dosyalarda yeniden sorulmaz.")
    headers = ingest.columns(open_upload(upload))
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

if own:
    # Portföy görünümü için son özet; tahmin önbelleğini bozmamak için sürüm artırılmadan yazılır.
    _summary = pipeline.portfolio_summary(res)
    if json.loads(store.get("portfolio_summary", "{}")).get("ozet") != _summary:
        store.set_quiet("portfolio_summary", json.dumps({"ozet": _summary, "hesap": f"{pd.Timestamp.now():%Y-%m-%d %H:%M}"}))


def record(invoice_id, kind, value=""):
    """Olayı panelde seçili tarihe yazar; bugünse saatiyle birlikte."""
    day = pd.Timestamp(as_of)
    now = pd.Timestamp.now()
    store.add_event(invoice_id, kind, value, now if day.date() == now.date() else day + pd.Timedelta(hours=12))
    st.rerun()


overview.render(res, store, own, BUSINESSES)

tab_cash_view, tab_collect_view, tab_accuracy_view = st.tabs(["Kasa tahmini", "Tahsilat işleri", "Tahmin doğruluğu"])
with tab_cash_view:
    tab_cash.render(res, res_key)
with tab_accuracy_view:
    tab_accuracy.render(res, res_key, store, own)
with tab_collect_view:
    if own:                     # imza dışındaki mesaj ve e-posta ayarları yalnızca kendi verinde var
        tab_collect.render(res, res_key, store, own, seller, record, iban, bank, mail)
    else:
        tab_collect.render(res, res_key, store, own, seller, record)
