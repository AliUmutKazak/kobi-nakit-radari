"""Sentetik KOBİ alacak verisi.

Gerçek veri gelene kadar geliştirme ve geri test için kullanılır. Gecikmeler bilerek
Gaussyen değildir: sağa çarpık, müşteriye göre kümelenmiş, zamanla kötüleşen ve
"ödeme günü" (ayın 15'i / ay sonu) alışkanlığına oturan bir yapı üretir.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

_NAMES = ["Anadolu", "Marmara", "Ege", "Toros", "Bosfor", "Kuzey", "Yıldız", "Demir", "Akın", "Güven"]
_KINDS = ["Yapı", "Tekstil", "Gıda", "Lojistik", "Makine", "Plastik", "Kimya", "Mobilya", "Otomotiv", "Ambalaj"]


def generate(seed: int = 7, n_customers: int = 40, months: int = 24, as_of="2026-10-01",
             trend: float = 0.6, shock: float = 0.0, season_amp: float = 0.0, season_peak: int = 11,
             inflation: float = 0.0, delay_scale: float = 1.0, terms_scale: float = 1.0,
             size_sigma: float = 0.6, cheque_share: float = 0.0, cheque_term: float = 75.0,
             cheque_bounce: float = 0.034, partial_share: float = 0.0) -> pd.DataFrame:
    """Tüm gerçeği (true_paid_date dahil) içeren fatura tablosunu üretir.

    Senaryo laboratuvarı boyutları (varsayılanlarla eski veri birebir üretilir):
    season_amp / season_peak: satış sayısında yıllık mevsimsellik, 1 + A cos(2π(ay − tepe)/12) (gerçek bir KOBİ'de
    A = 0,30, tepe kasım; UCI Online Retail II). inflation: fatura tutarlarının yıllık nominal artışı.
    delay_scale / terms_scale: gecikmeleri ve vadeleri ölçekler (tahsil süresini sektör dağılımına oturtmak için). size_sigma: müşteri
    büyüklüğünün log-normal yayılımı (büyük = cironun birkaç müşteride toplanması).
    cheque_share: müşterilerin çekle ödeyen payı. Çekle ödeyen müşterinin faturası çek alındığında kapanır
    (true_paid_date), para çekin vadesinde gelir (true_cash_date); vade log-normal, ortancası cheque_term gün;
    çek `cheque_bounce` olasılıkla karşılıksız çıkar ve para ufuk içinde gelmez (TBB Risk Merkezi, tutar
    bazında %2,8-3,4). cheque_share > 0 ise tabloya pay_method, true_cheque_due, true_cash_date eklenir.
    partial_share: faturalarını iki taksitte kapatan (havaleyle ödeyen) müşterilerin payı. İlk taksit tutarın
    %30-70'i, fatura tarihiyle son ödeme arasında bir gün gelir; fatura son taksitle kapanır. partial_share > 0 ise
    tabloya true_partial_date ve partial_frac eklenir."""
    rng = np.random.default_rng(seed)
    rng_lab = np.random.default_rng(seed + 10_000)          # yeni boyutlar ayrı akış: eski veri değişmez
    rng_part = np.random.default_rng(seed + 30_000)         # kısmi ödeme ayrı akış: diğer senaryolar değişmez
    as_of = pd.Timestamp(as_of)
    start = as_of - pd.DateOffset(months=months)
    n_days = (as_of - start).days
    # Piyasa şoku: her çeyrekte tüm müşterilerin gecikmesini birlikte oynatan, önceden bilinemeyen çarpan.
    quarters = pd.period_range(start, as_of, freq="Q")
    market = pd.Series(np.exp(shock * rng.standard_normal(len(quarters))), index=quarters)
    frames = []
    for i in range(n_customers):
        terms = int(rng.choice([30, 45, 60, 90], p=[0.35, 0.25, 0.30, 0.10]))
        if terms_scale != 1.0:
            terms = max(1, int(round(terms * terms_scale)))
        p_ontime = rng.beta(2, 2)
        base_delay = rng.gamma(2.0, 7.0) * delay_scale
        sigma = rng.uniform(0.5, 1.0)
        pay_day = int(rng.choice([0, 15, 31], p=[0.5, 0.25, 0.25]))
        rate = min(rng.pareto(2.0) * 1.5 + 0.4, 8.0)
        size = np.exp(size_sigma / 0.6 * np.log(rng.lognormal(0, 0.6)))   # aynı çekiliş, ölçeklenmiş yayılım
        p_default = 0.08 if rng.random() < 0.10 else rng.uniform(0, 0.02)

        k = rng.poisson(rate * months * (1 + season_amp))
        if k == 0:
            continue
        offs = rng.integers(0, n_days, k)
        if season_amp > 0:                                    # inceltme: ortalama fatura sayısı değişmez
            months_of = (start + pd.to_timedelta(offs, unit="D")).month
            keep = rng_lab.random(k) < (1 + season_amp * np.cos(2 * np.pi * (months_of - season_peak) / 12)) / (1 + season_amp)
            offs = offs[keep]
            k = len(offs)
            if k == 0:
                continue
        issue = start + pd.to_timedelta(offs, unit="D")
        due = issue + pd.Timedelta(days=terms)
        # Finansal sıkılaşma: dönem ilerledikçe gecikmeler uzar; Ocak ve Ağustos'ta ek sarkma.
        macro = (1 + trend * offs / n_days + 0.25 * np.isin(issue.month, [1, 8])) \
            * market.reindex((issue + pd.Timedelta(days=terms)).to_period("Q")).to_numpy()
        amount = rng.lognormal(np.log(45_000 * size), 0.8, k)
        z = (np.log(amount) - np.log(45_000 * size)) / 0.8
        if inflation:
            amount = amount * (1 + inflation) ** ((offs - n_days) / 365)   # bugünkü fiyatlarla aynı ölçek
        ontime = rng.random(k) < p_ontime / macro
        late = rng.lognormal(np.log(base_delay * macro + 3 * delay_scale), sigma) * np.clip(1 + 0.15 * z, 0.5, 2.0)
        delay = np.where(ontime, rng.normal(-1, 2, k), late).round()
        paid = pd.DatetimeIndex(due + pd.to_timedelta(delay, unit="D"))
        if pay_day == 31:
            paid = paid + pd.offsets.MonthEnd(0)
        elif pay_day == 15:
            first = paid.to_period("M").to_timestamp()
            nxt = (paid.to_period("M") + 1).to_timestamp()
            paid = pd.DatetimeIndex(np.where(paid.day <= 15, first, nxt)) + pd.Timedelta(days=14)
        paid = paid.where(rng.random(k) >= p_default, pd.NaT)  # hiç ödenmeyenler
        cheque = {}
        if cheque_share > 0:
            by_cheque = rng_lab.random() < cheque_share
            term = np.round(rng_lab.lognormal(np.log(cheque_term), 0.35, k)) if by_cheque else np.zeros(k)
            due_c = (paid + pd.to_timedelta(term, unit="D")) if by_cheque else pd.DatetimeIndex([pd.NaT] * k)
            bounced = rng_lab.random(k) < cheque_bounce
            cheque = {"pay_method": np.where(paid.isna(), None, "cek" if by_cheque else "havale"),
                      "true_cheque_due": due_c, "true_cash_date": (due_c.where(~bounced, pd.NaT) if by_cheque else paid)}

        partial = {}
        if partial_share > 0:
            # Çekle ödeyen müşteri taksit yapmaz (çek tek seferde verilir); ayrı akış, eski veri değişmez.
            splits = rng_part.random() < partial_share and not (cheque_share > 0 and by_cheque)
            frac = np.where(splits & paid.notna(), rng_part.uniform(0.3, 0.7, k), 0.0)
            span = (paid - issue).days.to_numpy(dtype=float)
            first_pay = issue + pd.to_timedelta(np.round(np.nan_to_num(span) * rng_part.uniform(0.3, 0.7, k)), unit="D")
            partial = {"true_partial_date": pd.DatetimeIndex(first_pay).where(frac > 0, pd.NaT), "partial_frac": frac}

        frames.append(pd.DataFrame({
            "customer_id": f"C{i:03d}",
            "customer_name": f"{rng.choice(_NAMES)} {rng.choice(_KINDS)} {i:02d} A.Ş.",
            "vkn": f"{rng.integers(10**9, 10**10 - 1)}",
            "issue_date": issue, "due_date": due,
            "amount": amount.round(2), "true_paid_date": paid,
        } | cheque | partial))
    full = pd.concat(frames, ignore_index=True).sort_values("issue_date").reset_index(drop=True)
    full.insert(0, "invoice_id", [f"FTR{2025000000 + i}" for i in range(len(full))])
    return full


def observe(full: pd.DataFrame, as_of, record_lag: int = 0) -> pd.DataFrame:
    """`as_of` tarihinde görülebilen veri: gelecekteki faturalar ve ödemeler gizlenir.

    record_lag: tahsilat kayıtları bu kadar gün geride (kayıt günü gününe değil ya da dosya önceden alınmış); son
    `record_lag` günde gelen ödemeler kayıtta yoktur, faturaları açık görünür. Faturalar zamanında kayıtlıdır."""
    as_of = pd.Timestamp(as_of)
    df = full[full["issue_date"] <= as_of].copy()
    df["paid_date"] = df["true_paid_date"].where(df["true_paid_date"] <= as_of - pd.Timedelta(days=record_lag))
    df["open_amount"] = np.where(df["paid_date"].isna(), df["amount"], 0.0)
    if "true_partial_date" in df:
        # Kayıtların son gününe kadar gelen ilk taksit açık tutarı azaltır (banka ekstresiyle eşleşen kısmi ödeme).
        cut = as_of - pd.Timedelta(days=record_lag)
        part = df["paid_date"].isna() & (df["true_partial_date"] <= cut)
        df.loc[part, "open_amount"] = df.loc[part, "amount"] * (1 - df.loc[part, "partial_frac"])
        df = df.drop(columns=["true_partial_date", "partial_frac"])
    if "true_cheque_due" in df:
        # Çek alındığında vadesi bilinir (cari hesaba "çek" açıklamasıyla ve vadesiyle işlenir); karşılıksız
        # çıkıp çıkmayacağı ve paranın gerçek geliş günü bilinmez.
        df["cheque_due"] = df["true_cheque_due"].where(df["paid_date"].notna())
        df = df.drop(columns=["true_cheque_due", "true_cash_date", "pay_method"])
    return df.drop(columns="true_paid_date").reset_index(drop=True)


def payment_events(full: pd.DataFrame, as_of, record_lag: int = 0) -> pd.DataFrame:
    """Kayıtların son gününe kadar görülen tahsilat olayları (date, invoice_id, amount): banka ekstresiyle
    eşleşen her ödeme ayrı olaydır (reconcile.collection_events ile aynı biçim). Taksitli faturada ilk taksit ve
    kapanış ayrı olaylardır."""
    cut = pd.Timestamp(as_of) - pd.Timedelta(days=record_lag)
    frac = full["partial_frac"] if "partial_frac" in full else pd.Series(0.0, index=full.index)
    closed = full["true_paid_date"] <= cut
    out = [pd.DataFrame({"date": full.loc[closed, "true_paid_date"], "invoice_id": full.loc[closed, "invoice_id"],
                         "amount": full.loc[closed, "amount"] * (1 - frac[closed])})]
    if "true_partial_date" in full:
        first = full["true_partial_date"] <= cut
        out.append(pd.DataFrame({"date": full.loc[first, "true_partial_date"], "invoice_id": full.loc[first, "invoice_id"],
                                 "amount": full.loc[first, "amount"] * frac[first]}))
    return pd.concat(out, ignore_index=True).sort_values("date").reset_index(drop=True)


def cheque_portfolio(obs: pd.DataFrame, as_of) -> pd.DataFrame | None:
    """`as_of` günü elde olan, vadesi gelmemiş çekler (date = vade): panelin çek/senet portföyü girdisi."""
    if "cheque_due" not in obs:
        return None
    hit = obs["cheque_due"] > pd.Timestamp(as_of)
    return pd.DataFrame({"date": obs.loc[hit, "cheque_due"], "amount": obs.loc[hit, "amount"],
                         "label": obs.loc[hit, "customer_name"]}).reset_index(drop=True)


def cash_plan(obs: pd.DataFrame, as_of, horizon: int = 90, opening_months: float = 0.45):
    """Açılış kasası ve deterministik çıkışlar (kira, maaş, SGK/muhtasar, KDV, tedarikçi)."""
    as_of = pd.Timestamp(as_of)
    monthly = obs.loc[obs["issue_date"] > as_of - pd.Timedelta(days=180), "amount"].sum() / 6
    rows = []
    for d in pd.date_range(as_of + pd.Timedelta(days=1), periods=horizon):
        fixed = {1: ("Kira", 0.06), 5: ("Maaş", 0.30), 26: ("SGK + Muhtasar", 0.10), 28: ("KDV", 0.08)}
        if d.day in fixed:
            label, share = fixed[d.day]
            rows.append((d, monthly * share, label))
        if d.dayofweek == 4:
            rows.append((d, monthly * 0.46 / 4.33, "Tedarikçi ödemeleri"))
    return opening_months * monthly, pd.DataFrame(rows, columns=["date", "amount", "label"])


def export_samples(folder, seed: int = 7, as_of: str = "2026-10-01") -> None:
    """Kendi verisini yükleyecek kullanıcı için örnek dosyalar (Türkçe başlık ve sayı biçimiyle)."""
    from pathlib import Path
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)
    obs = observe(generate(seed=seed, as_of=as_of), as_of)
    tr = dict(sep=";", decimal=",", index=False, date_format="%d.%m.%Y", encoding="utf-8-sig")

    obs.rename(columns={"invoice_id": "Fatura No", "customer_name": "Cari Unvan", "vkn": "VKN",
                        "issue_date": "Fatura Tarihi", "due_date": "Vade Tarihi", "amount": "Tutar"})[
        ["Fatura No", "Cari Unvan", "VKN", "Fatura Tarihi", "Vade Tarihi", "Tutar"]].to_csv(folder / "faturalar.csv", **tr)

    paid = obs.dropna(subset=["paid_date"]).groupby(["customer_id", "customer_name", "vkn", "paid_date"], as_index=False)["amount"].sum()
    with_vkn = rng.random(len(paid)) < 0.6
    paid["Açıklama"] = ("GELEN HAVALE " + paid["customer_name"].str.upper() + " "
                        + np.where(with_vkn, paid["vkn"], "") + " CARI HESAP ODEMESI")
    paid.rename(columns={"paid_date": "Tarih", "amount": "Tutar"})[["Tarih", "Tutar", "Açıklama"]]         .sort_values("Tarih").to_csv(folder / "ekstre.csv", **tr)

    # Aynı veri, Mikro cari hareket föyü biçiminde: borç = fatura, alacak = tahsilat.
    sales = pd.DataFrame({"Evrak Tarihi": obs["issue_date"], "Evrak No": obs["invoice_id"], "Cari İsmi": obs["customer_name"],
                          "Vade Tarihi": obs["due_date"], "Açıklama": "Satış Faturası", "Borç": obs["amount"], "Alacak": 0.0})
    receipts = pd.DataFrame({"Evrak Tarihi": paid["paid_date"], "Evrak No": "", "Cari İsmi": paid["customer_name"],
                             "Vade Tarihi": pd.NaT, "Açıklama": "Gelen havale", "Borç": 0.0, "Alacak": paid["amount"]})
    pd.concat([sales, receipts]).sort_values("Evrak Tarihi", kind="stable").to_csv(folder / "cari_ekstre.csv", **tr)

    opening, outflows = cash_plan(obs, as_of)
    supplier = outflows["label"] == "Tedarikçi ödemeleri"
    outflows[~supplier].rename(columns={"date": "Tarih", "amount": "Tutar", "label": "Kalem"}) \
        .to_csv(folder / "giderler.csv", **tr)
    # Haftalık tedarikçi ödemeleri, ayrı borç faturaları olarak (her hafta 2-3 fatura).
    vendors = ["Delta Hammadde Ltd.", "Kuzey Ambalaj A.Ş.", "Ege Nakliyat Ltd.", "Marmara Enerji A.Ş."]
    rows = []
    for k, r in enumerate(outflows[supplier].itertuples()):
        parts = rng.dirichlet(np.ones(int(rng.integers(2, 4))))
        for j, share in enumerate(parts):
            rows.append({"Fatura No": f"ALS{2026000 + 10 * k + j}", "Tedarikçi": vendors[(k + j) % len(vendors)],
                         "Fatura Tarihi": r.date - pd.Timedelta(days=30), "Vade": r.date,
                         "Tutar": round(r.amount * share, 2)})
    pd.DataFrame(rows).to_csv(folder / "odenecekler.csv", **tr)

    as_of = pd.Timestamp(as_of)
    names = obs["customer_name"].drop_duplicates().sample(8, random_state=seed).to_numpy()
    pd.DataFrame({"Vade": as_of + pd.to_timedelta(rng.integers(5, 80, 8), unit="D"),
                  "Tutar": rng.lognormal(np.log(120_000), 0.5, 8).round(2), "Keşideci": names})         .sort_values("Vade").to_csv(folder / "cekler.csv", **tr)
    (folder / "OKU.txt").write_text("\n".join([
        f"Örnek dosyalar {as_of:%d.%m.%Y} tarihine göre üretildi; panelde 'Bugünün tarihi' olarak bunu seçin.",
        f"Açılış kasası için {opening:.0f} TL girebilirsiniz.",
        "Tedarikçi ödemeleri odenecekler.csv dosyasındadır; gerçekçi bir tablo için giderler.csv ile birlikte yükleyin.",
        "cari_ekstre.csv aynı satışları cari hesap ekstresi biçiminde içerir; faturalar.csv + ekstre.csv yerine tek başına yüklenebilir.",
        ""]), encoding="utf-8")


def to_ubl_xml(row, with_due_date: bool = True) -> str:
    """Test ve örnek dosyalar için asgari bir UBL-TR faturası."""
    due = (f"<cac:PaymentMeans><cbc:PaymentMeansCode>42</cbc:PaymentMeansCode>"
           f"<cbc:PaymentDueDate>{pd.Timestamp(row['due_date']).date()}</cbc:PaymentDueDate></cac:PaymentMeans>"
           ) if with_due_date else ""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
 xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
 xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
  <cbc:UBLVersionID>2.1</cbc:UBLVersionID>
  <cbc:CustomizationID>TR1.2</cbc:CustomizationID>
  <cbc:ID>{row['invoice_id']}</cbc:ID>
  <cbc:IssueDate>{pd.Timestamp(row['issue_date']).date()}</cbc:IssueDate>
  <cbc:DocumentCurrencyCode>TRY</cbc:DocumentCurrencyCode>
  <cac:AccountingCustomerParty><cac:Party>
    <cac:PartyIdentification><cbc:ID schemeID="VKN">{row['vkn']}</cbc:ID></cac:PartyIdentification>
    <cac:PartyName><cbc:Name>{row['customer_name']}</cbc:Name></cac:PartyName>
  </cac:Party></cac:AccountingCustomerParty>
  {due}
  <cac:LegalMonetaryTotal><cbc:PayableAmount currencyID="TRY">{row['amount']:.2f}</cbc:PayableAmount></cac:LegalMonetaryTotal>
</Invoice>"""
