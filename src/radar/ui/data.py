"""Panelin veri katmanı: yüklenen dosyaların ayrıştırılması, işletme kaydı ve önbellekli hesaplar."""
import hashlib
import io
import json
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

from radar import actions, anonymize, ingest, pilot, pipeline
from radar.reconcile import collection_events, reconcile
from radar.store import Store, create_business, list_businesses
from radar.ui.fmt import tl

KEEP = ("sim", "ranked", "metrics", "opening", "gap_day", "simple_model", "n_train", "disputed_total", "obs", "as_of",
        "ctx", "outflows", "info")
MAPPABLE = {"invoices": ("Fatura dosyası", ingest.INVOICE_FIELDS, ingest.INVOICE_REQUIRED),
            "payments": ("Banka ekstresi", ingest.PAYMENT_FIELDS, ingest.PAYMENT_REQUIRED)}


def retro_data_key(store, res) -> str:
    """Aşama 0 sonucunun hangi verilerle üretildiği: yüklenen dosyaların özeti ve tahmin tarihi."""
    return "|".join([store.get(f"hash_{n}", "") for n in ("invoices", "payments")] + [str(res["as_of"])[:10]])


@st.cache_resource
def get_store(path: str) -> Store:
    return Store(path)


def secret_key(store: Store) -> str:
    return anonymize.business_key(anonymize.load_or_create_key(), store.business_id)


def open_upload(upload):
    buf = io.BytesIO(upload.getvalue())
    buf.name = upload.name
    return buf


def save_upload(store: Store, name: str, uploads, parse) -> None:
    """Dosya değiştiyse ayrıştırıp kaydeder; aynı dosya yeniden çizimde tekrar yazılmaz."""
    uploads = [u for u in (uploads if isinstance(uploads, list) else [uploads]) if u]
    if not uploads:
        return
    mapping = store.get(f"map_{name}", "{}") + (store.get("rates", "") + store.get("terms", "")
                                                 if name in ("invoices", "payables", "outflows", "cheques") else "")
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


def parse_bank(store: Store, uploads):
    """Banka ekstresi: girişler tahsilat tablosuna, çıkışlar gider planı kontrolü için ayrı tabloya."""
    ins, outs, notes, last = ingest.bank_movements(open_upload(uploads[0]), json.loads(store.get("map_payments", "{}")),
                                                   with_balance=True)
    store.set("bank_balance", f"{last[1]:.2f}" if last else "")
    store.set("bank_balance_date", f"{last[0]:%Y-%m-%d}" if last else "")
    # Yalnızca tarih ve tutar saklanır: açıklamada çalışan ya da tedarikçi adı bulunabilir ve kontrol için gerekmez
    # (KVKK m.4/2-ç: amaçla bağlantılı, sınırlı ve ölçülü işleme).
    store.save("bank_outflows", outs[["date", "amount"]])
    return ins, notes


def parse_invoices(store: Store, uploads, terms, rates):
    frames, notes = [], []
    xml = [open_upload(u) for u in uploads if u.name.lower().endswith(".xml")]
    ledger_cheques, ledger_events = [], []
    for u in uploads:
        if not u.name.lower().endswith(".xml") and ingest.is_ledger(open_upload(u)):
            df, n, chq, ev = ingest.load_ledger(open_upload(u), terms, fallback_customer=Path(u.name).stem, with_events=True)
            frames.append(df)
            notes += n
            ledger_cheques.append(chq)
            ledger_events.append(ev)
        elif not u.name.lower().endswith(".xml"):
            df, n = ingest.load_invoices(open_upload(u), terms, json.loads(store.get("map_invoices", "{}")), rates)
            frames.append(df)
            notes += n
    responses = pd.DataFrame(columns=["invoice_id", "response", "response_date"])
    if xml:
        inv_xml, resp_xml, n = ingest.read_xml(xml)
        notes += n
        responses = ingest.parse_responses(resp_xml, notes)
        if inv_xml:
            df, n = ingest.load_ubl(inv_xml, terms, rates)
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
    combined = pd.concat(frames, ignore_index=True).drop_duplicates("invoice_id")
    # e-Fatura uygulama yanıtları (KABUL, RED, IADE) hangi dosyadan gelirse gelsin faturalara işlenir.
    if len(responses) or "scenario" in combined:
        combined = ingest.apply_responses(combined, responses, notes)
    dup = ingest.possible_duplicates(combined)
    if len(dup):
        first = dup.iloc[0]
        notes.append(f"{int(dup['n'].sum())} fatura, aynı müşteriye aynı gün aynı tutarla kesilmiş görünüyor ({len(dup)} grup; "
                     f"ör. {first['customer_name']}, {first['issue_date']:%d.%m.%Y}: {first['invoice_ids']}). Aynı fatura "
                     "iki kez girildiyse (ör. elle ve e-faturadan) dosyadan birini çıkarın; aksi hâlde alacak iki kez sayılır. "
                     "Gerçekten ayrı faturalarsa bir şey yapmanız gerekmez.")
    return combined, notes


@st.cache_data(show_spinner="Demo şirketin 90 günlük kasası hesaplanıyor; 10-20 saniye sürer. Panel açık kaldıkça sonraki işlemler anında gelir...")
def run_demo(seed: int, include_projected: bool, today: str):
    res = pipeline.demo(seed=seed, as_of=today, include_projected=include_projected)
    return {k: res[k] for k in KEEP} | {"notes": [], "has_outflows": True, "unmatched": None, "last_activity": None}


@st.cache_data(show_spinner="Verileriniz işleniyor ve 90 günlük kasa hesaplanıyor; 10-20 saniye sürebilir. Veri değişmedikçe sonraki işlemler anında gelir...")
def run_own(path: str, rev: int, as_of: str, include_projected: bool):
    """`rev` kayıt her değiştiğinde artar; sonuç ancak o zaman yeniden hesaplanır. `path` işletmeyi ayırır."""
    store = get_store(path)
    notes = [n for name in ("invoices", "payments", "payables", "outflows") for n in json.loads(store.get(f"notes_{name}", "[]"))]
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
        unknown = ingest.holiday_years_unknown(plan["date"]) if len(plan) else []
        if unknown:
            notes.append(f"{', '.join(map(str, unknown))} yılının Ramazan ve Kurban Bayramı tarihleri programda henüz yok; "
                         "vergi ödeme günleri yalnızca hafta sonu ve sabit tarihli tatillere göre kaydırıldı. Program "
                         "güncellenmeli (Diyanet resmî tatil listesi).")
        plan = plan.assign(kaynak="Aylık sabit giderler", tur="Varsayım (elle girilen)")
        outflows = plan if outflows is None else pd.concat([outflows, plan], ignore_index=True)
    if payables is not None:
        flows, n = ingest.payables_to_outflows(payables, as_of)
        notes += n + [f"Ödenecek faturalar: {len(payables)} adet, {tl(payables['amount'].sum())}."]
        flows = flows.assign(kaynak="Ödenecek faturalar", tur="Kesin (borç faturası)")
        outflows = flows if outflows is None else pd.concat([outflows, flows], ignore_index=True)
    if cheques is not None:
        notes.append(f"Çek/senet portföyü: {len(cheques)} adet, {tl(cheques['amount'].sum())}.")
    promises = actions.promise_reliability(store.events(), obs, as_of)
    if promises:
        worst = ", ".join(f"{c} ({k})" for c, k in list(promises["broken_by_customer"].items())[:3])
        notes.append(f"Tarihi geçmiş {promises['n']} ödeme sözünün {promises['kept']} tanesi (%{promises['rate'] * 100:.0f}) söz "
                     "tarihinde ya da öncesinde tutuldu." + (f" En çok söz tutmayan: {worst}." if worst else "")
                     + " Tahmin, sözü yeni vade sayar ama müşterinin gerçek gecikme alışkanlığını da uygular.")
    # Gider planı, işletmenin kendi banka çıkışlarıyla karşılaştırılır; eksikse fark tahmini olarak eklenir.
    extra, gap = pipeline.unplanned_outflows(store.load("bank_outflows"), outflows, as_of)
    if gap is not None:
        notes.append(f"Son {gap['span_days']} günde bankadan ayda ortalama {tl(gap['hist_month'])} ödeme çıktı; önümüzdeki "
                     f"90 gün için planlanan giderler ayda {tl(gap['plan_month'])}.")
        if len(extra) and store.get("auto_unplanned", "1") == "1":
            notes.append(f"Aradaki fark (ayda {tl(gap['gap_month'])}) plan dışı ödemeler olarak kasa planına eklendi: "
                         "plan eksikse kasa olduğundan dolu görünür. Bu farkı oluşturan ödemeler (ör. tek seferlik yatırım, "
                         "kendi hesaplarınız arası aktarım) bir daha olmayacaksa \"Diğer ayarlar\"dan kapatabilirsiniz.")
            extra = extra.assign(kaynak="Banka ekstresi (geçmiş ortalama)", tur="Tahmin (plan dışı)")
            outflows = extra if outflows is None else pd.concat([outflows, extra], ignore_index=True)
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
                            payments_through=through, events=events, outflow_history=store.load("bank_outflows"))
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



@st.cache_data(show_spinner=False)
def run_scenario(key, _res, collect_ids, delay_labels, delay_days):
    return pipeline.scenario(_res, collect_ids, delay_labels=delay_labels, delay_days=delay_days)


@st.cache_data(show_spinner="Geçmiş tarihlere dönülüp tahmin yeniden üretiliyor; yarım dakikayı bulabilir...")
def run_backtest(obs, as_of):
    return pipeline.backtest_own(obs, as_of)


@st.cache_data(show_spinner="Pilot raporu hazırlanıyor; geçmiş tarihlerde test de yapıldığı için yarım dakika kadar sürer...")
def run_pilot(key, _res, label, hide, retro_json="", store_path=""):
    secret = secret_key(get_store(store_path)) if hide else None
    retro = pd.read_json(io.StringIO(retro_json), orient="records") if retro_json else None
    r = pilot.build(_res["obs"], _res["as_of"], res=_res, label=label, key=secret,
                    unmatched=_res.get("unmatched"), n_payments=_res.get("n_payments"), retro=retro,
                    opening_date=get_store(store_path).get("opening_date") or None)
    return pilot.render(r).encode("utf-8")


def anonymous_package(store: Store, seller: str):
    extra = {"giderler": store.load("outflows"), "odenecekler": store.load("payables"), "cekler": store.load("cheques")}
    retro_json = store.get("retro_result", "")
    retro = pd.read_json(io.StringIO(retro_json), orient="records") if retro_json else None
    margins = json.loads(store.get("b1_margins", "{}")) or None
    return anonymize.package(seller or "İşletme", store.load("invoices"), secret_key(store),
                             store.load("payments"), extra, records=store.pilot_records(), retro=retro, margins=margins)



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
    sample.set("opening_date", f"{pd.Timestamp(today):%Y-%m-%d}")   # tanıtımda "kasa tutarı tarihi yok" uyarısı çıkmasın
    sample.set("seller", "Örnek Ticaret A.Ş. (MERSİS 0000000000000000)")
    st.session_state["active_business"] = SAMPLE_NAME


def add_business():
    try:
        create_business(st.session_state.get("new_business", ""))
        st.session_state["active_business"] = " ".join(st.session_state["new_business"].split())
        st.session_state["new_business"] = ""
    except ValueError as err:
        st.session_state["business_error"] = str(err)
