"""Uçtan uca akış: veri -> model -> simülasyon -> öncelikli tahsilat listesi, ve geri testler."""
from __future__ import annotations

import os

import numpy as np
import pandas as pd

from . import actions
from .features import build_features
from .model import DelayModel, FallbackModel, evaluate, fit_model, training_frame
from .simulate import (CHEQUE_BOUNCE, RECAL_GRID, pit_recalibration, PRIOR_RHO, aging_curve, censored_normal_fit, conditional_scores, correlation_from_scores,
                       simulate)
from .synthetic import cash_plan, observe


def default_rates(obs: pd.DataFrame, as_of, prior_n: float = 20.0) -> pd.Series:
    """Müşteri bazında tahsil edilememe oranı: vadesi 180+ gün geçmiş faturalardan, büzülmüş."""
    old = obs[obs["due_date"] <= pd.Timestamp(as_of) - pd.Timedelta(days=180)]
    bad = old["paid_date"].isna()
    g = bad.mean() if len(old) else 0.02
    by = bad.groupby(old["customer_id"]).agg(["sum", "count"])
    rate = (by["sum"] + prior_n * g) / (by["count"] + prior_n)
    return rate.reindex(obs["customer_id"].unique()).fillna(g)


def cheque_habits(obs: pd.DataFrame, as_of, prior_n: float = 10.0, window_days: int = 365,
                  min_terms: int = 5) -> dict | None:
    """Müşterilerin çekle ödeme alışkanlığı, işletmenin kendi cari hesabından öğrenilir.

    Cari hesapta çek alındığında fatura kapanır, para çekin vadesinde gelir. Bu fark hesaba katılmazsa
    çekle ödeyen müşterilerin açık faturaları ve yeni satışları kasaya vadeden önce girmiş görünür (iyimser
    hata). Türkiye'de çekle tahsilatın payını ve çek vadesini veren kurumsal bir istatistik yoktur (TCMB ve
    TBB karşılıksızlık oranını yayımlar); bu yüzden iki değer de işletmenin son bir yıllık ödemelerinden alınır:
    - pay: müşteri bazında çekle kapanan fatura oranı, işletme ortalamasına büzülmüş (prior_n fatura),
    - vade: müşterinin kendi çek vadeleri (en az `min_terms` çek varsa), yoksa işletmenin tüm çek vadeleri.
    Çek bilgisi (cheque_due) yoksa ya da hiç çek yoksa None döner ve tahmin eskisi gibidir."""
    if "cheque_due" not in obs:
        return None
    as_of = pd.Timestamp(as_of)
    paid = obs[obs["paid_date"].notna() & (obs["paid_date"] <= as_of)
               & (obs["paid_date"] > as_of - pd.Timedelta(days=window_days))]
    is_chq = paid["cheque_due"].notna()
    if not is_chq.any():
        return None
    overall = float(is_chq.mean())
    by = is_chq.groupby(paid["customer_id"]).agg(["sum", "count"])
    share = (by["sum"] + prior_n * overall) / (by["count"] + prior_n)
    terms = (paid.loc[is_chq, "cheque_due"] - paid.loc[is_chq, "paid_date"]).dt.days.clip(lower=0)
    pools = {c: t.to_numpy() for c, t in terms.groupby(paid.loc[is_chq, "customer_id"]) if len(t) >= min_terms}
    return {"share": share, "overall": overall, "pools": pools, "terms": terms.to_numpy(),
            "n": int(is_chq.sum()), "median_term": float(np.median(terms))}


def _cheque_args(habits: dict | None, inv: pd.DataFrame, n_sims: int, seed: int) -> dict:
    if habits is None:
        return {}
    rng = np.random.default_rng(seed + 13)
    cust = inv["customer_id"].to_numpy()
    p = pd.Series(cust).map(habits["share"]).fillna(habits["overall"]).to_numpy(float)
    terms = np.empty((len(inv), n_sims), dtype=np.int64)
    for i, c in enumerate(cust):
        terms[i] = rng.choice(habits["pools"].get(c, habits["terms"]), n_sims)
    return {"cheque_p": p, "cheque_terms": terms}


def installment_habits(obs: pd.DataFrame, events: pd.DataFrame | None, as_of, prior_n: float = 10.0,
                       window_days: int = 365, min_n: int = 5, tol: float = 0.01) -> dict | None:
    """Müşterilerin faturalarını taksitle kapatma alışkanlığı, işletmenin kendi tahsilat olaylarından öğrenilir.

    Model ödemeyi faturanın kapandığı günde öğrenir. Taksitle ödeyen müşteride ilk taksit bundan önce gelir; bu
    hesaba katılmazsa tahmin kötümser kalır. Laboratuvarda müşterilerin %40'ı taksitle öderken orta tahmin
    −0,13 aylık ciro sapıyordu (LAB_RAPORU.md, sürüm 4). Son bir yılda kapanan faturalardan:
    - pay: müşteri bazında birden çok tahsilatla kapanan fatura oranı, işletme ortalamasına büzülmüş,
    - ilk taksidin tutar oranı ve zamanı (fatura günüyle kapanış günü arasındaki yeri, 0-1): müşterinin kendi
      örnekleri (en az `min_n`), yoksa işletmenin bütün örnekleri.
    events: tahsilat olayları (date, invoice_id, amount; reconcile.collection_events). Yoksa ya da hiç taksit
    yoksa None döner ve tahmin eskisi gibidir."""
    if events is None or not len(events):
        return None
    as_of = pd.Timestamp(as_of)
    closed = obs[obs["paid_date"].notna() & (obs["paid_date"] <= as_of)
                 & (obs["paid_date"] > as_of - pd.Timedelta(days=window_days))]
    if not len(closed):
        return None
    ev = events[(events["date"] <= as_of) & events["invoice_id"].isin(closed["invoice_id"])]
    ev = ev.sort_values("date")
    first = ev.groupby("invoice_id").agg(first_date=("date", "first"), first_amount=("amount", "first"), n=("amount", "size"))
    inv = closed.set_index("invoice_id").join(first, how="left")
    span = (inv["paid_date"] - inv["issue_date"]).dt.days
    split = ((inv["n"] > 1) & (inv["first_date"] < inv["paid_date"])
             & (inv["first_amount"] < inv["amount"] * (1 - tol)) & (span > 0)).fillna(False)
    if not split.any():
        return None
    overall = float(split.mean())
    by = split.groupby(inv["customer_id"]).agg(["sum", "count"])
    share = (by["sum"] + prior_n * overall) / (by["count"] + prior_n)
    sp = inv[split]
    frac = (sp["first_amount"] / sp["amount"]).clip(0.01, 0.99).to_numpy()
    u = ((sp["first_date"] - sp["issue_date"]).dt.days / span[split]).clip(0, 1).to_numpy()
    pairs = np.column_stack([frac, u])
    pools = {c: pairs[(sp["customer_id"] == c).to_numpy()] for c in sp["customer_id"].unique()
             if (sp["customer_id"] == c).sum() >= min_n}
    return {"share": share, "overall": overall, "pools": pools, "pairs": pairs, "n": int(split.sum()),
            "median_frac": float(np.median(frac))}


def _split_args(habits: dict | None, inv: pd.DataFrame, n_sims: int, seed: int) -> dict:
    if habits is None:
        return {}
    rng = np.random.default_rng(seed + 17)
    cust = inv["customer_id"].to_numpy()
    p = pd.Series(cust).map(habits["share"]).fillna(habits["overall"]).to_numpy(float)
    # Kısmen ödenmiş açık faturanın kalanı zaten biliniyor: yeni taksit simüle edilmez.
    p = np.where(inv["open_amount"].to_numpy(float) < inv["amount"].to_numpy(float) * 0.99, 0.0, p)
    frac = np.empty((len(inv), n_sims)); u = np.empty((len(inv), n_sims))
    for i, c in enumerate(cust):
        pool = habits["pools"].get(c, habits["pairs"])
        pick = pool[rng.integers(0, len(pool), n_sims)]
        frac[i], u[i] = pick[:, 0], pick[:, 1]
    return {"split_p": p, "split_frac": frac, "split_u": u}


def unplanned_outflows(bank_out: pd.DataFrame | None, planned: pd.DataFrame | None, as_of, horizon: int = 90,
                       window_days: int = 90, min_history_days: int = 60) -> tuple[pd.DataFrame, dict | None]:
    """Gider planının eksiksizliği, işletmenin kendi banka çıkışlarıyla karşılaştırılır.

    Kasa tahmininde giderler kullanıcının girdiği plandan gelir. Plan eksikse (unutulan vergi, SGK, tedarikçi,
    kredi taksidi) kasa olduğundan dolu görünür; küçük işletmede en sık hata kaynağı budur. Son `window_days`
    günde bankadan çıkan aylık ortalama tutar, önümüzdeki `horizon` gün için planlanan aylık ortalamayla
    karşılaştırılır. Plan geçmişin altındaysa fark "plan dışı ödemeler (tahmini)" olarak haftalık eşit
    paylarla eklenir. Dayanak: ihtiyatlılık; giderler olduğundan düşük gösterilmez (KGK Kavramsal Çerçeve
    md. 142; 1 Sıra No.lu Muhasebe Sistemi Uygulama Genel Tebliği). Rakam bir eşikten değil, işletmenin kendi
    banka geçmişinden gelir. Banka geçmişi `min_history_days`'ten kısaysa karşılaştırma yapılmaz.
    Dönen: (eklenecek satırlar: date, amount, label; özet ya da None)."""
    empty = pd.DataFrame(columns=["date", "amount", "label"])
    if bank_out is None or not len(bank_out):
        return empty, None
    as_of = pd.Timestamp(as_of)
    hist = bank_out[bank_out["date"] <= as_of]
    if not len(hist):
        return empty, None
    end = hist["date"].max()
    span = min(window_days, (end - hist["date"].min()).days + 1)
    if span < min_history_days:
        return empty, None
    recent = hist[hist["date"] > end - pd.Timedelta(days=span)]
    hist_month = float(recent["amount"].sum()) / span * 30.4
    plan = planned if planned is not None else empty
    in_h = plan[(pd.to_datetime(plan["date"]) > as_of) & (pd.to_datetime(plan["date"]) <= as_of + pd.Timedelta(days=horizon))]
    plan_month = float(in_h["amount"].sum()) / horizon * 30.4
    gap = hist_month - plan_month
    info = {"hist_month": hist_month, "plan_month": plan_month, "gap_month": max(gap, 0.0), "span_days": span}
    if gap <= 0:
        return empty, info
    weeks = int(np.ceil(horizon / 7))
    days = [as_of + pd.Timedelta(days=7 * w + 7) for w in range(weeks)]
    days = [d for d in days if d <= as_of + pd.Timedelta(days=horizon)]
    per = gap * horizon / 30.4 / len(days)
    rows = pd.DataFrame({"date": days, "amount": per, "label": "Plan dışı ödemeler (banka geçmişinden, tahmini)"})
    return rows, info


def payments_cutoff(obs: pd.DataFrame, as_of, window_days: int = 90, alpha: float = 0.05):
    """Tahsilatların kayda hangi güne kadar işlendiği, kayıtlardan tahmin edilir.

    Faturalar (e-fatura) genelde zamanında kayıtlıdır; tahsilat kayıtları ise yasal süre içinde olsa da günü gününe
    olmayabilir (VUK m.219: muameleler deftere 10 günden fazla geciktirilmeden, muhasebe fişi ve bordroya dayanan kayıtlarda esas deftere en geç 45 günde işlenir), ya da panele yüklenen dosya muhasebe programından birkaç gün önce alınmış olabilir.
    Bu durumda gerçekte ödenmiş faturalar açık görünür ve para hem bugünkü kasada hem gelecek tahsilatta
    sayılır. Laboratuvarda 7 günlük gecikme kötümser uç aşımını %7'den %43'e çıkardı (LAB_RAPORU.md).

    Kural: son tahsilattan bugüne geçen boşluk, işletmenin son 90 günlük tahsilat sıklığında (Poisson) %5'ten
    az olasılıkla görülecek kadar uzunsa tahsilat kayıtları son tahsilat gününde kesilmiş sayılır; değilse
    kayıtlar günceldir. Kullanıcı gerçek tarihi biliyorsa (ör. "muhasebe 30 Eylül'e kadar işledi") o esas alınır."""
    as_of = pd.Timestamp(as_of)
    paid = obs.loc[obs["paid_date"].notna() & (obs["paid_date"] <= as_of), "paid_date"]
    if not len(paid):
        return as_of
    last = paid.max()
    days = paid[paid > last - pd.Timedelta(days=window_days)].dt.normalize().nunique()
    rate = days / window_days                                  # tahsilat görülen gün oranı
    gap = (as_of - last).days
    if rate <= 0 or rate >= 1:
        return as_of if gap <= 1 else last
    # Gün başına "en az bir tahsilat" olasılığı rate; gap gün hiç tahsilat görülmeme olasılığı (1 - rate)^gap.
    return last if (1 - rate) ** gap < alpha else as_of


SEASON_DAYS = 364                 # 52 hafta: geçen yılın aynı dönemi, haftanın günü korunur
GROWTH_DAYS = 182                 # yıllık büyüme: son 26 haftanın satışı / geçen yılın aynı 26 haftası
GROWTH_CLIP = (0.5, 2.0)
SALES_GROWTH = os.environ.get("RADAR_SALES_GROWTH", "1") == "1"      # "0": yalnızca karşılaştırma deneyleri için


def sales_growth(obs: pd.DataFrame, as_of) -> float:
    """İşletmenin yıllık nominal satış büyümesi: son 26 haftanın satışının geçen yılın aynı 26 haftasına oranı.

    "Geçen yılın aynı dönemi" tahmini geçen yılın fiyatlarıyla yapılır; yüksek enflasyonda (TÜİK TÜFE 2021-2025
    yıllık %20-85) bu, yeni satışları sistematik olarak düşük gösterir. Mevsimsel naif tahmini yıllık değişim
    oranıyla ölçeklemek yerleşik bir yöntemdir (Hyndman ve Athanasopoulos, Forecasting: Principles and Practice,
    mevsimsel naif ve sürüklenme yöntemleri). Oran mevsimsellikten etkilenmez (iki pencere yılın aynı haftaları).

    Oran gürültülüdür: log oranın standart hatası (se) iki penceredeki haftalık satışların değişkenliğinden (delta
    yöntemi) hesaplanır ve oran pozitif kısımlı James-Stein kestiricisiyle 1'e doğru büzülür (James ve Stein 1961;
    Efron ve Morris 1973): log g × max(0, 1 − se² / (log g)²). Belirgin büyüme (ör. yüksek enflasyon) büyük ölçüde
    uygulanır, gürültü düzeyindeki oran uygulanmaz. Enflasyonun düşük olduğu gerçek bir KOBİ verisinde (UCI Online
    Retail II) oranı büzmeden uygulamak yalnızca gürültü ekledi. Geçmiş yetmezse 1; aşırı değerler 0,5-2'ye kırpılır."""
    as_of = pd.Timestamp(as_of)
    if obs["issue_date"].min() > as_of - pd.Timedelta(days=SEASON_DAYS + GROWTH_DAYS):
        return 1.0
    weeks = []
    for end in (as_of, as_of - pd.Timedelta(days=SEASON_DAYS)):
        part = obs[(obs["issue_date"] > end - pd.Timedelta(days=GROWTH_DAYS)) & (obs["issue_date"] <= end)]
        k = ((end - part["issue_date"]).dt.days // 7).clip(upper=GROWTH_DAYS // 7 - 1)
        weeks.append(part.groupby(k)["amount"].sum().reindex(range(GROWTH_DAYS // 7), fill_value=0.0).to_numpy())
    now, before = (w.sum() for w in weeks)
    if now <= 0 or before <= 0:
        return 1.0
    log_g = np.log(now / before)
    se2 = sum(w.var(ddof=1) / len(w) / w.mean() ** 2 for w in weeks)
    shrunk = log_g * max(0.0, 1.0 - se2 / log_g ** 2) if log_g else 0.0
    return float(np.clip(np.exp(shrunk), *GROWTH_CLIP))


def _sales_shift(obs: pd.DataFrame, as_of, horizon: int, method: str) -> pd.DataFrame:
    """`method` ile as_of'tan sonraki `horizon` gün için öngörülen faturalar (henüz kesilmemiş satışlar).
    Tutarlar, kaydırılan süre kadar işletmenin yıllık büyümesiyle ölçeklenir (sales_growth)."""
    as_of = pd.Timestamp(as_of)
    lag = SEASON_DAYS if method == "mevsimsel" else horizon
    shift = pd.Timedelta(days=lag)
    src = obs[(obs["issue_date"] > as_of - shift) & (obs["issue_date"] <= as_of - shift + pd.Timedelta(days=horizon))].copy()
    src["invoice_id"] = "PRJ-" + src["invoice_id"].astype(str)
    src["issue_date"] += shift
    src["due_date"] += shift
    src["paid_date"] = pd.NaT
    if SALES_GROWTH:
        # Kaydırılan dönem kadar büyüme: mevsimselde bir yıllık, son dönem hızında ufuk kadar (g ** (ufuk / 364)).
        src["amount"] = src["amount"] * sales_growth(obs, as_of) ** (lag / SEASON_DAYS)
    src["open_amount"] = src["amount"]
    return src


def sales_method(obs: pd.DataFrame, as_of, horizon: int) -> str:
    """Yeni satış yöntemi, işletmenin kendi geçmişinde zaman sırasına uygun geri testle seçilir (Tashman 2000;
    Hyndman ve Athanasopoulos, Forecasting: Principles and Practice): "mevsimsel" (geçen yılın aynı dönemi) ile
    "hiz" (son dönemin hızı) aynı geçmiş haftalarda 30 günlük satışı tahmin eder; mutlak log hatası küçük olan
    seçilir. Mevsimsel yöntem için en az bir yıl + bir ay geçmiş, karşılaştırma için en az 8 ortak hafta gerekir;
    yoksa son dönemin hızı kullanılır.

    Gerekçe: gerçek bir KOBİ'de (UCI Online Retail II, mevsimsel satış) 90 günlük sapma son dönem hızıyla %37,
    geçen yılın aynı dönemiyle %7; mevsimselliği olmayan, büyüyen sentetik şirketlerde ise tersi. İki tür işletme de
    gerçekte vardır; tek bir genel kural ikisine birden uymaz."""
    first = obs["issue_date"].min()
    if first > pd.Timestamp(as_of) - pd.Timedelta(days=SEASON_DAYS + SALES_BLOCK):
        return "hiz"
    seasonal = sales_errors(obs, as_of, horizon, "mevsimsel")
    if len(seasonal) < 8:
        return "mevsimsel"
    rate = sales_errors(obs, as_of, horizon, "hiz")[:len(seasonal)]      # aynı (en yakın) haftalar
    from .standards import SIGNIFICANCE, diebold_mariano
    # Mevsimsel yönteme yalnızca anlamlı biçimde daha isabetliyse geçilir (Diebold-Mariano, %5): iki yöntemin
    # hataları yakınsa gürültüye göre karar verilmez. Haftalık 30 günlük pencereler ~5 hafta üst üste biner.
    dm = diebold_mariano(np.abs(seasonal), np.abs(rate), overlap=int(np.ceil(SALES_BLOCK / 7)))
    return "mevsimsel" if dm["p_better"] < SIGNIFICANCE else "hiz"


def project_sales(obs: pd.DataFrame, as_of, horizon: int) -> pd.DataFrame:
    """Henüz kesilmemiş faturalar (bkz. sales_method)."""
    return _sales_shift(obs, as_of, horizon, sales_method(obs, as_of, horizon))


SALES_BLOCK = 30                  # yeni satış belirsizliği aylık bloklarla: blok başına ayrı düzey katsayısı


def sales_errors(obs: pd.DataFrame, as_of, horizon: int, method: str, window: int = SALES_BLOCK,
                 step: int = 7) -> np.ndarray:
    """Aynı yöntemin işletmenin kendi geçmişindeki satış tahmini hataları: log(gerçekleşen / tahmin), `window`
    günlük pencerelerde.

    Her hafta geriye gidilir; o gün bilinenle sonraki `window` günün satışı aynı yöntemle (`method`) tahmin edilir
    ve gerçekleşenle karşılaştırılır. Yöntemin uygulanamadığı (geçmişi yetmeyen) tarihler alınmaz: başka bir
    yöntemin hataları karıştırılırsa belirsizlik ve düzey bozulur. Bu dağılım simülasyonda satış düzeyinin
    belirsizliğidir (konformal yaklaşım: varsayımdan değil, işletmenin kendi geçmiş hatalarından)."""
    as_of = pd.Timestamp(as_of)
    first = obs["issue_date"].min()
    lag = SEASON_DAYS if method == "mevsimsel" else horizon
    out = []
    s = as_of - pd.Timedelta(days=window)
    while s - pd.Timedelta(days=lag) >= first:
        known = obs[obs["issue_date"] <= s]
        src = _sales_shift(known, s, horizon, method)
        pred = float(src.loc[src["issue_date"] <= s + pd.Timedelta(days=window), "amount"].sum())
        actual = float(obs.loc[(obs["issue_date"] > s) & (obs["issue_date"] <= s + pd.Timedelta(days=window)), "amount"].sum())
        if pred > 0 and actual > 0:
            out.append(np.log(actual / pred))
        s -= pd.Timedelta(days=step)
    return np.asarray(out)


def censor(obs: pd.DataFrame, t) -> pd.DataFrame:
    """Tablonun `t` tarihinde görünen hâli: sonraki faturalar ve ödemeler gizlenir."""
    t = pd.Timestamp(t)
    df = obs[obs["issue_date"] <= t].copy()
    df["paid_date"] = df["paid_date"].where(df["paid_date"] <= t)
    df["open_amount"] = np.where(df["paid_date"].isna(), df["amount"], 0.0)
    return df                                   # satır numaraları korunur: önceden hesaplanmış özelliklerle eşleşir


def calibrate(obs: pd.DataFrame, as_of, origins: int = 4, step: int = 90, mature_days: int = 60,
              min_scores: int = 100, shrink_n: float = 200.0, feats: pd.DataFrame | None = None) -> dict:
    """Simülasyonun belirsizlik ayarlarını, geçmişteki ileriye dönük tahminlerin hatasından çıkarır.

    Son `origins` çeyreğin her birinin başına dönülür, o günkü bilgiyle model kurulur ve o gün
    açık olan faturaların gecikmesi tahmin edilir. Gerçekleşenle karşılaştırınca:
    - gerçekleşenin koşullu tahmin dağılımındaki yeri (PIT) tekdüze değilse dağılım parametresiz
      yeniden ayarlanır (Kaplan-Meier ile, ödenmemiş fatura sansürlü; bkz. simulate.pit_recalibration).
      Açık verilerde model, vadesi yaklaşan faturaların yakında ödenme olasılığını sistematik olarak
      düşük veriyordu; tek bir kayma/ölçek sayısı bunu düzeltemiyordu (DOGRULAMA.md, 16 Ekim 2026),
    - çeyrekler arası ve müşteriler arası ortak hareket -> korelasyonlar,
    - aynı tarihlerde toplam tahsilat simüle edilip gerçekleşenle karşılaştırılır; bant, geçmiş
      hataların %80'ini içine alacak kadar genişletilir (konformal; daraltılmaz). Büyük portföyde
      fatura düzeyindeki korelasyon tahmini toplam belirsizliği küçümsüyordu.
    Yeniden ayar, vadesi gelmemiş ("fresh") ve vadesi geçmiş ("overdue") faturalar için ayrıdır.
    Modelin kendi eğitim verisindeki uyumu bunları ölçemez; o veri bilinen geçmiştir."""
    as_of = pd.Timestamp(as_of)
    neutral = {"z_shift": 0.0, "z_scale": 1.0, "n": 0}
    default = {"rho_market": PRIOR_RHO[0], "rho_customer": PRIOR_RHO[1], "fresh": neutral, "overdue": neutral}
    final = obs.set_index("invoice_id")
    feats = build_features(obs) if feats is None else feats
    parts, stored = [], []
    for k in range(1, origins + 1):
        t = as_of - pd.Timedelta(days=k * step)
        past = censor(obs, t)
        if not len(past):
            break
        X, y = training_frame(past, t, feats=feats)
        if len(X) < 60:
            break
        # Sonucu seçim yanlılığı olmadan bilinenler: o gün açık ve bugün itibarıyla olgunlaşmış faturalar.
        test = past[past["paid_date"].isna() & (past["due_date"] <= as_of - pd.Timedelta(days=mature_days))]
        if "disputed" in test:
            test = test[~test["disputed"].fillna(False).astype(bool)]
        if len(test) < 10:
            continue
        outcome = final.loc[test["invoice_id"]]
        delay = (outcome["paid_date"].fillna(as_of) - outcome["due_date"]).dt.days.to_numpy()
        d0 = (t - test["due_date"]).dt.days.to_numpy()
        Q = fit_model(X, y).predict(build_features(past, ref=t).loc[test.index])
        stored.append((k, t, test, Q, aging_curve(past, t), past))
        parts.append(pd.DataFrame({"z": conditional_scores(Q, delay, d0, aging_curve(past, t)), "origin": str(k),
                                   "customer_id": test["customer_id"].to_numpy(), "overdue": d0 > 0,
                                   "censored": outcome["paid_date"].isna().to_numpy()}))
    if not parts:
        return default
    scores = pd.concat(parts, ignore_index=True)
    if len(scores) < min_scores:
        return default

    def group(part: pd.DataFrame) -> dict:
        n = len(part)
        if n < 30:
            return neutral | {"n": n}
        return {"z_shift": 0.0, "z_scale": 1.0, "n": n,
                "recal": pit_recalibration(part["z"].to_numpy(), part["censored"].to_numpy(), 30.0)}

    rho_m, rho_c = correlation_from_scores(scores["z"].to_numpy(), scores["origin"], scores["customer_id"])
    calib = {"rho_market": rho_m, "rho_customer": rho_c,
             "fresh": group(scores[~scores["overdue"]]), "overdue": group(scores[scores["overdue"]])}
    calib["widen"], calib["widen_n"] = aggregate_widen(stored, final, as_of, calib)
    return calib


def aggregate_widen(stored, final, as_of, calib, horizons=(14, 30, 60, 90), level: float = 0.8,
                    n_sims: int = 400, cap: float = 3.0) -> tuple[float, int]:
    """Toplam tahsilat düzeyinde konformal genişletme katsayısı.

    Her geçmiş tahmin tarihinde, o gün açık (ve sonucu bilinen) faturalardan h gün içinde gelecek tahsilat
    simüle edilir; gerçekleşenin bant yarı genişliğine oranı (normalleştirilmiş aşım) hesaplanır. Bu oranların
    konformal %80 kantili 1'den büyükse bant o kadar genişletilir; daraltılmaz (az gözlemle daraltmak riskli)."""
    errs = []
    for k, t, test, Q, aging, past in stored:
        inv = test.assign(p_default=test["customer_id"].map(default_rates(past, t)).to_numpy(), projected=False)
        H = min(max(horizons), (as_of - t).days)
        if H < min(horizons):
            continue
        sim = simulate(inv, Q, t, 0.0, pd.DataFrame({"date": [], "amount": []}), H, n_sims, seed=100 + k,
                       aging=aging, **{**_sim_args(calib, inv, t), "widen": 1.0})
        paid = final.loc[test["invoice_id"], "paid_date"]
        amount = test["amount"].to_numpy(float)
        for h in horizons:
            if h > H:
                continue
            actual = float(amount[((paid > t) & (paid <= t + pd.Timedelta(days=h))).to_numpy()].sum())
            lo, med, hi = sim.p10[h], sim.p50[h], sim.p90[h]
            half = (hi - med) if actual >= med else (med - lo)
            if half > 0:
                errs.append(abs(actual - med) / half)
    if len(errs) < 4:
        return 1.0, len(errs)
    errs = np.sort(errs)
    q = errs[min(len(errs) - 1, int(np.ceil((len(errs) + 1) * level)) - 1)]
    return float(min(max(1.0, q), cap)), len(errs)


def forecast(obs: pd.DataFrame, as_of, opening: float, outflows: pd.DataFrame, horizon: int = 90,
             n_sims: int = 2000, include_projected: bool = True, seed: int = 0,
             cheques: pd.DataFrame | None = None, calib_hook=None, cheque_aware: bool = True,
             cheque_by_customer: bool = False, payments_through=None, payday_snap: bool = False,
             events: pd.DataFrame | None = None, installment_aware: bool = True) -> dict:
    """calib_hook: kalibrasyon sözlüğünü değiştiren isteğe bağlı fonksiyon (deneyler ve pilot sırasındaki
    çevrimiçi kantil izleme için; bkz. pilot.online_adjustment).
    cheque_aware: çekle ödeyen müşterilerde paranın çek vadesinde gelmesi (cheque_habits; yalnızca deneylerde kapatılır).
    payments_through: tahsilatların kayda işlendiği son gün (bkz. payments_cutoff). Daha eskiyse model, kalibrasyon
    ve gecikme eğrileri o güne göre kurulur; arada gelmiş olabilecek paralar bugünkü kasanın içinde sayılır.
    events: tahsilat olayları (reconcile.collection_events); kısmi tahsilatlardan taksit alışkanlığı öğrenilir
    (installment_habits; installment_aware=False yalnızca deneylerde).
    payday_snap: ödemeyi müşterinin ödeme gününe oturtma (simulate.snap_to_payday). Laboratuvarda denendi, aralık
    skorunu iyileştirmedi (LAB_RAPORU.md); kapalıdır, seçenek deneyin tekrarlanabilmesi için duruyor."""
    as_of = pd.Timestamp(as_of)
    ref =min(pd.Timestamp(payments_through), as_of) if payments_through is not None else as_of
    lag = int((as_of - ref).days)
    feats_issue = build_features(obs)
    X, y = training_frame(obs, ref, feats=feats_issue)
    model = fit_model(X, y)

    obs = obs.copy()
    obs["disputed"] = obs["disputed"].fillna(False).astype(bool) if "disputed" in obs else False
    obs["promised_date"] = pd.to_datetime(obs["promised_date"]) if "promised_date" in obs else pd.NaT
    is_open = obs["open_amount"] > 0
    # İtirazlı faturalar çözülene kadar ne tahmine ne hatırlatma listesine girer.
    open_inv = obs[is_open & ~obs["disputed"]].assign(projected=False)
    parts = [open_inv]
    sales_level, method, errs = None, None, np.array([])
    if include_projected:
        method = sales_method(obs, as_of, horizon)
        proj = _sales_shift(obs, as_of, horizon, method)
        proj["sales_block"] = ((proj["issue_date"] - as_of).dt.days.clip(lower=1) - 1) // SALES_BLOCK
        parts.append(proj.assign(projected=True, disputed=False, promised_date=pd.NaT))
        errs = sales_errors(obs, as_of, horizon, method)
        if len(errs) < 8 and method == "mevsimsel":
            errs = sales_errors(obs, as_of, horizon, "hiz")        # genişlik için daha uzun geçmişli yöntemin hataları
        if len(errs) >= 8:
            # Aylık blok başına satış düzeyi: geçmiş 30 günlük hatalardan yeniden örneklenir. Az geçmişte faturaları
            # tek tek yeniden örnekleyen eski yönteme dönülür (gerçek KOBİ verisinde o yöntem fazla dardı).
            n_blocks = int(np.ceil(horizon / SALES_BLOCK))
            # Geçmişten yalnızca belirsizliğin genişliği alınır: katsayının ortalaması 1'e eşitlenir. Kısa geçmişte
            # ortalama sapma tahmini gürültülüdür ve orta tahmini kaydırır; ortancaya göre merkezlemek ise üç bloğun
            # toplamını yukarı iter (log-normal toplamın ortancası, ortancaların toplamından büyüktür).
            level = np.exp(np.random.default_rng(seed + 7).choice(errs, (n_blocks, n_sims), replace=True))
            sales_level = level / level.mean(axis=1, keepdims=True)
    target = pd.concat(parts, ignore_index=True)
    # Özellikler bugünün bilgisiyle hesaplanır; tahmin edilen faturalar geçmişe karışmaz.
    combined = pd.concat([obs[~is_open], target], ignore_index=True)
    feats = build_features(combined, ref=ref).iloc[-len(target):].reset_index(drop=True)
    target["p_default"] = target["customer_id"].map(default_rates(obs, ref)).to_numpy()

    # Ödeme sözü verilmiş faturada söz tarihi yeni vade sayılır; müşterinin olağan
    # gecikme alışkanlığı bu tarihe göre uygulanır (varsayım: söz de vade kadar tutulur).
    promised = target["promised_date"] > as_of
    sim_inv = target.assign(due_date=target["promised_date"].where(promised, target["due_date"]))
    calib = calibrate(obs, ref, feats=feats_issue)
    if calib_hook is not None:
        calib = calib_hook(calib)
    habits = cheque_habits(obs, ref) if cheque_aware else None
    splits = installment_habits(obs, events, ref) if installment_aware else None
    ctx = {"sim_inv": sim_inv, "Q": model.predict(feats), "aging": aging_curve(obs, ref), "cheques": cheques,
           "horizon": horizon, "n_sims": n_sims, "seed": seed, "calib": calib, "sales_level": sales_level,
           "cheque_args": _cheque_args(habits, sim_inv, n_sims, seed)
           | ({"cheque_by_customer": cheque_by_customer} if habits else {}) | ({"lag": lag} if lag else {})
           | ({"payday": sim_inv["customer_id"].map(actions.payment_habits(obs[obs["paid_date"] <= ref])["payday"])
                         .fillna(0).astype(int).to_numpy()} if payday_snap else {}),
           "payments_through": ref, "lag": lag}
    ctx["cheque_args"] |= _split_args(splits, sim_inv, n_sims, seed)        # simülasyona giden ek ayarlar
    sim = simulate(sim_inv, ctx["Q"], as_of, opening, outflows, horizon, n_sims, seed=seed, aging=ctx["aging"],
                   cheques=cheques, sales_level=sales_level, **_sim_args(calib, sim_inv, ref), **ctx["cheque_args"])
    real = ~target["projected"].to_numpy()
    gap_day = sim.breach_day if sim.breach_day is not None else horizon
    ranked = actions.prioritize(target[real], sim.pay_day[real], as_of, gap_day, actions.payment_habits(obs), horizon)
    return {"as_of": as_of, "model": model, "simple_model": isinstance(model, FallbackModel), "n_train": len(X),
            "sim": sim, "ranked": ranked, "gap_day": gap_day, "metrics": actions.metrics(obs, as_of),
            "opening": opening, "outflows": outflows, "obs": obs, "ctx": ctx,
            "info": {"n_invoices": int(len(obs)), "n_train": int(len(X)), "n_customers": int(obs["customer_id"].nunique()),
                     "history_from": obs["issue_date"].min(), "simple_model": isinstance(model, FallbackModel),
                     "n_calibration": int(calib["fresh"]["n"] + calib["overdue"]["n"]),
                     "rho_market": calib["rho_market"], "rho_customer": calib["rho_customer"],
                     "widen": calib.get("widen", 1.0), "sales_method": method, "sales_errors_n": int(len(errs)),
                     "sales_error_spread": float(np.percentile(errs, 90) - np.percentile(errs, 10)) if len(errs) >= 8 else None,
                     "cheque_share": habits["overall"] if habits else None, "cheque_n": habits["n"] if habits else 0,
                     "cheque_median_term": habits["median_term"] if habits else None,
                     "payments_through": ref, "payments_lag": lag,
                     "installment_share": splits["overall"] if splits else None, "installment_n": splits["n"] if splits else 0},
            "disputed_total": float(obs.loc[is_open & obs["disputed"], "open_amount"].sum())}


def _sim_args(calib: dict, inv: pd.DataFrame, as_of) -> dict:
    overdue = (inv["due_date"] < pd.Timestamp(as_of)).to_numpy() & ~inv["projected"].to_numpy()
    pick = lambda key: np.where(overdue, calib["overdue"][key], calib["fresh"][key])
    grid = lambda g: np.asarray(calib[g].get("recal", RECAL_GRID))
    recal = np.where(overdue[:, None], grid("overdue")[None, :], grid("fresh")[None, :])
    return {"rho_market": calib["rho_market"], "rho_customer": calib["rho_customer"],
            "z_shift": pick("z_shift"), "z_scale": pick("z_scale"), "widen": calib.get("widen", 1.0), "recal": recal}


def scenario(res: dict, collect_ids=(), collect_in_days: int = 7, delay_labels=(), delay_days: int = 0):
    """Aynı rastgele senaryolarla "şu olsaydı" hesabı.

    collect_ids: bu faturalar `collect_in_days` gün içinde kesin tahsil edilmiş sayılır.
    delay_labels / delay_days: bu gider kalemleri o kadar gün ertelenir (ufkun dışına çıkan düşer)."""
    ctx, as_of = res["ctx"], res["as_of"]
    inv = ctx["sim_inv"].copy()
    hit = inv["invoice_id"].isin(list(collect_ids)) & ~inv["projected"]
    cash = float(inv.loc[hit, "open_amount"].sum())
    inv.loc[hit, "open_amount"] = 0.0          # satır yerinde kalır ki rastgele sayılar kaymasın
    out = res["outflows"].copy()
    if delay_days and len(out) and "label" in out:
        late = out["label"].isin(list(delay_labels))
        out.loc[late, "date"] = pd.to_datetime(out.loc[late, "date"]) + pd.Timedelta(days=delay_days)
    if cash:
        out = pd.concat([out, pd.DataFrame({"date": [as_of + pd.Timedelta(days=collect_in_days)],
                                            "amount": [-cash], "label": ["Tahsilat (senaryo)"]})], ignore_index=True)
    return simulate(inv, ctx["Q"], as_of, res["opening"], out, ctx["horizon"], ctx["n_sims"],
                    seed=ctx["seed"], **_sim_args(ctx["calib"], inv, ctx.get("payments_through", as_of)),
                    aging=ctx["aging"], cheques=ctx["cheques"], sales_level=ctx.get("sales_level"),
                    **ctx.get("cheque_args", {}))


SAFE_LEVEL = 0.10          # ürünün her yerindeki kötümser senaryo düzeyi (protokolde ön kayıtlı)


def safe_to_spend(sim, level: float = SAFE_LEVEL) -> float:
    """Güvenle harcanabilir tutar: bugün bundan fazlası harcanırsa önümüzdeki dönemde kasanın en az bir gün eksiye
    düşme olasılığı `level`'i aşar.

    Bugün S harcamak bütün senaryo yollarını S kadar aşağı kaydırır; "eksiye düşme olasılığı en çok %10" koşulu
    S'nin senaryo başına en düşük kasanın %10'luk yüzdeliğini geçmemesidir. Kasayı fazla göstermenin eksik
    göstermekten pahalı olduğu kararlarda en iyi tek sayı, maliyet oranına karşılık gelen yüzdeliktir (Gneiting
    2011, "Quantiles as optimal point forecasts", IJF 27(2)); %10 düzeyi, fazla göstermenin 9 kat pahalı sayılmasına
    karşılık gelir. Bant dürüst (kalibre) kalır, karar kötümser uçtan verilir (KGK Kavramsal Çerçeve md. 142:
    ihtiyatlılık, gelirlerin olduğundan yüksek gösterilmemesi; ama kasıtlı olarak düşük gösterilmesi de değil)."""
    return float(max(0.0, np.quantile(sim.min_balance, level)))


def _p10_min(paths: np.ndarray) -> float:
    """Kötümser (P10) kasa çizgisinin en düşük noktası: grafikteki bandın alt kenarı ve "en derin açık" ile aynı tanım."""
    return float(np.percentile(paths, 10, axis=0).min())


def invoice_impact(res: dict, invoice_ids) -> pd.Series:
    """Her fatura için: ufuk içinde hiç gelmezse kötümser (P10) en düşük kasa kaç TL düşer.

    Aynı senaryo yolları kullanılır; yalnızca o faturanın girişi çıkarılır. Önceliğin nedenini sayıyla
    gösterir: büyük ama zaten geç gelmesi beklenen bir fatura, küçük ama açığın olduğu haftada gelecek
    bir faturadan daha az etkili olabilir."""
    sim, inv = res["sim"], res["ctx"]["sim_inv"]
    if sim.paths is None:
        return pd.Series(dtype=float)
    base = _p10_min(sim.paths)
    days = np.arange(sim.paths.shape[1])
    rows = {str(i): k for k, i in enumerate(inv["invoice_id"].astype(str)) if not inv["projected"].iloc[k]}
    out = {}
    for i in map(str, invoice_ids):
        k = rows.get(i)
        if k is None:
            continue
        arrived = days[None, :] >= sim.pay_day[k][:, None]          # senaryo × gün: para gelmiş mi
        out[i] = base - _p10_min(sim.paths - inv["open_amount"].iloc[k] * arrived)
    return pd.Series(out, dtype=float)


def customer_delay(res: dict, customer_ids, days: int) -> dict:
    """Seçilen müşterilerin bugün açık faturaları `days` gün daha geç gelirse kasa bandı (aynı senaryolar).

    Ortak şok ve alacak yoğunlaşması sorusu: "en büyük müşterim bir ay geç öderse kasam ne olur?".
    Gelecek satışlar senaryoya dahil değildir (yalnızca bugün açık faturalar kayar)."""
    sim, inv = res["sim"], res["ctx"]["sim_inv"]
    hit = np.flatnonzero(inv["customer_id"].isin(list(customer_ids)).to_numpy() & ~inv["projected"].to_numpy())
    paths = sim.paths.copy()
    t = np.arange(paths.shape[1])[None, :]
    for k in hit:
        amount = float(inv["open_amount"].iloc[k])
        pd_k = sim.pay_day[k][:, None]
        paths -= amount * (t >= pd_k)                    # eski ödeme günü
        paths += amount * (t >= pd_k + days)             # yeni ödeme günü (ufkun dışına çıkan düşer)
    p10, p50, p90 = np.percentile(paths, [10, 50, 90], axis=0)
    return {"p10": p10, "p50": p50, "p90": p90, "amount": float(inv["open_amount"].iloc[hit].sum()),
            "prob_any_breach": float((paths.min(axis=1) < 0).mean()), "p10_min": _p10_min(paths),
            "p10_min_before": _p10_min(sim.paths)}


def fx_exposure(res: dict) -> pd.DataFrame:
    """Bugün açık dövizli alacak: para birimi, orijinal tutar, girilen kur ve TL karşılığı."""
    obs = res["obs"]
    if "currency" not in obs:
        return pd.DataFrame()
    fx = obs[(obs["open_amount"] > 0) & (obs["currency"].fillna("TRY") != "TRY")]
    if fx.empty:
        return pd.DataFrame()
    rate = fx["fx_rate"] if "fx_rate" in fx else pd.Series(np.nan, index=fx.index)
    return (fx.assign(original=fx["open_amount"] / rate, rate=rate)
            .groupby("currency").agg(original=("original", "sum"), rate=("rate", "first"), tl=("open_amount", "sum"))
            .reset_index())


def fx_shift(res: dict, pct: float) -> dict:
    """TL, dövizlere karşı `pct` kadar değer kaybederse (eksi: kazanırsa) bugün açık dövizli faturalardan gelecek
    TL tutarı o oranda değişir; aynı senaryolarla kasa bandı. Kur tahmini değil, kullanıcının senaryosudur.
    Dövizli borçlar (ödenecekler) dosyada TL olduğundan kapsam dışıdır."""
    sim, inv = res["sim"], res["ctx"]["sim_inv"]
    currency = inv["currency"].fillna("TRY") if "currency" in inv else pd.Series("TRY", index=inv.index)
    hit = np.flatnonzero((currency != "TRY").to_numpy() & ~inv["projected"].to_numpy())
    paths = sim.paths.copy()
    t = np.arange(paths.shape[1])[None, :]
    for k in hit:
        paths += float(inv["open_amount"].iloc[k]) * pct * (t >= sim.pay_day[k][:, None])
    p10, p50, p90 = np.percentile(paths, [10, 50, 90], axis=0)
    return {"p10": p10, "p50": p50, "p90": p90, "prob_any_breach": float((paths.min(axis=1) < 0).mean()),
            "p10_min": _p10_min(paths), "p10_min_before": _p10_min(sim.paths)}


def gap_summary(res: dict, max_k: int = 40, collect_in_days: int = 7) -> dict:
    """Kötümser senaryodaki açığın derinliği ve onu kapatmak için listeden kaç fatura gerektiği.

    k = None: listedeki ilk `max_k` faturanın tamamı tahsil edilse de açık kapanmıyor."""
    sim = res["sim"]
    out = {"gap": float(max(0.0, -sim.p10.min())), "gap_day": int(sim.p10.argmin()), "k": 0, "amount": 0.0}
    if sim.breach_day is None:
        return out
    todo = res["ranked"][res["ranked"]["actionable"]].head(max_k)
    ids = list(todo["invoice_id"])
    closes = lambda k: scenario(res, ids[:k], collect_in_days).breach_day is None
    if not ids or not closes(len(ids)):
        return out | {"k": None, "amount": float(todo["open_amount"].sum())}
    lo, hi = 1, len(ids)                       # daha çok tahsilat hiçbir zaman zarar vermez: ikili arama güvenli
    while lo < hi:
        mid = (lo + hi) // 2
        lo, hi = (lo, mid) if closes(mid) else (mid + 1, hi)
    return out | {"k": lo, "amount": float(todo["open_amount"].head(lo).sum())}


def weekly_table(res: dict, weeks: int = 13) -> pd.DataFrame:
    """13 haftalık haftalık plan. Bilinen kalemler (giderler, borçlar) ile tahmine dayananlar
    (açık faturalardan ve henüz kesilmemiş satışlardan beklenen tahsilat) ayrı sütunlardadır."""
    sim, ctx, as_of = res["sim"], res["ctx"], res["as_of"]
    inv = ctx["sim_inv"]
    amount = inv["open_amount"].to_numpy(float)
    projected = inv["projected"].to_numpy(bool)
    out = res["outflows"]
    out_off = (pd.to_datetime(out["date"]) - as_of).dt.days.to_numpy() if len(out) else np.array([])
    out_amt = out["amount"].to_numpy(float) if len(out) else np.array([])
    cheques = ctx.get("cheques")
    rows = []
    for w in range(weeks):
        lo, hi = 7 * w + 1, min(7 * (w + 1), len(sim.p50) - 1)
        if lo > hi:
            break
        in_week = ((sim.pay_day >= lo) & (sim.pay_day <= hi)).mean(axis=1) * amount
        chq = 0.0
        if cheques is not None and len(cheques):
            c_off = (pd.to_datetime(cheques["date"]) - as_of).dt.days.to_numpy()
            chq = float(cheques["amount"].to_numpy(float)[(c_off >= lo) & (c_off <= hi)].sum() * (1 - CHEQUE_BOUNCE))
        rows.append({"Hafta": f"{(as_of + pd.Timedelta(days=lo)):%d.%m} – {(as_of + pd.Timedelta(days=hi)):%d.%m}",
                     "Açık faturalardan beklenen (TL)": float(in_week[~projected].sum()) + chq,
                     "Yeni satışlardan beklenen (TL)": float(in_week[projected].sum()),
                     "Bilinen çıkışlar (TL)": float(out_amt[(out_off >= lo) & (out_off <= hi)].sum()),
                     "Hafta sonu kasa, kötümser (TL)": float(sim.p10[hi]),
                     "Hafta sonu kasa, orta (P50) (TL)": float(sim.p50[hi]),
                     "Eksiye düşme olasılığı": float(sim.prob_negative[lo:hi + 1].max())})
    return pd.DataFrame(rows)


def backtest_model(full: pd.DataFrame, as_of, holdout_days: int = 240) -> dict:
    """Zaman bazlı ayrım: kesim tarihine kadar eğit, sonrasında kesilen olgun faturalarda ölç."""
    as_of = pd.Timestamp(as_of)
    cutoff = as_of - pd.Timedelta(days=holdout_days)
    X_tr, y_tr = training_frame(observe(full, cutoff), cutoff)
    model = DelayModel().fit(X_tr, y_tr)
    obs = observe(full, as_of)
    X, y = training_frame(obs, as_of)
    test = obs.loc[X.index, "issue_date"] > cutoff
    return evaluate(model.predict(X[test]), y[test], X.loc[test, "hist_med"])


def naive_collections(obs: pd.DataFrame, book: pd.DataFrame, as_of, end) -> dict:
    """Üç basit yöntemle `as_of`tan `end`e kadar `book` (o gün açık faturalar) içinden tahsil edilecek tutar.

    vade: vadesi `end`e kadar gelen (ya da geçmiş) her fatura ödenir. medyan: her fatura, müşterinin `obs`taki
    geçmiş gecikme medyanı kadar geç ödenir (geçmişi olmayan müşteride genel medyan). oran: aynı uzunluktaki
    bir önceki dönemde, dönem başında açık olan alacağın yüzde kaçı tahsil edildiyse bugün de o kadarı
    tahsil edilir (muhasebede yaygın "tahsilat oranı" yaklaşımı). İlk iki yöntem vadesi çoktan geçmiş
    faturaları "yakında ödenir" sayar; şüpheli alacağı çok olan işletmede oran yöntemi en güçlü rakiptir."""
    as_of, end = pd.Timestamp(as_of), pd.Timestamp(end)
    prev = as_of - (end - as_of)
    before = obs[(obs["issue_date"] <= prev) & ~(obs["paid_date"] <= prev)]
    base = before["amount"].sum()
    rate = before.loc[before["paid_date"] <= as_of, "amount"].sum() / base if base > 0 else float("nan")
    paid = obs.dropna(subset=["paid_date"])
    lateness = (paid["paid_date"] - paid["due_date"]).dt.days
    overall = float(lateness.median()) if len(paid) else 0.0
    delay = pd.to_timedelta(book["customer_id"].map(lateness.groupby(paid["customer_id"]).median())
                            .fillna(overall).round(), unit="D")
    return {"naive_due": float(book.loc[book["due_date"] <= end, "amount"].sum()),
            "naive_median": float(book.loc[book["due_date"] + delay <= end, "amount"].sum()),
            "naive_rate": float(rate * book["amount"].sum())}


def backtest_collections(full: pd.DataFrame, as_of, horizon: int = 90, origins: int = 6, step: int = 30,
                         n_sims: int = 1000) -> pd.DataFrame:
    """Geçmiş tarihlerde tahmin üretip, sonraki `horizon` günde gerçekleşen tahsilatla karşılaştırır."""
    as_of = pd.Timestamp(as_of)
    rows = []
    for k in range(origins):
        t = as_of - pd.Timedelta(days=horizon + k * step)
        obs = observe(full, t)
        res = forecast(obs, t, 0.0, pd.DataFrame({"date": [], "amount": []}), horizon, n_sims,
                       include_projected=False, seed=k)
        was_open = (full["issue_date"] <= t) & ~(full["true_paid_date"] <= t)
        end = t + pd.Timedelta(days=horizon)
        got = was_open & (full["true_paid_date"] <= end)
        actual = full.loc[got, "amount"].sum()
        lo, mid, hi = np.percentile(res["sim"].collections, [10, 50, 90])
        naive = naive_collections(obs, full[was_open], t, end)
        pct = lambda pred: (pred - actual) / actual * 100 if actual else float("nan")   # tahsilatsız dönem
        rows.append({"origin": t.date(), "actual": actual, "p10": lo, "p50": mid, "p90": hi,
                     "inside": lo <= actual <= hi, "err_p50_pct": pct(mid), **naive,
                     "err_due_pct": pct(naive["naive_due"]), "err_median_pct": pct(naive["naive_median"]),
                     "err_rate_pct": pct(naive["naive_rate"])})
    return pd.DataFrame(rows)


def backtest_own(obs: pd.DataFrame, as_of, horizon: int = 90, origins: int = 4, step: int = 30,
                 min_history_days: int = 180) -> pd.DataFrame | None:
    """Kullanıcının kendi verisinde tahsilat geri testi; geçmiş yetersizse None döner.

    En eski test tarihinden önce en az `min_history_days` günlük fatura geçmişi aranır."""
    as_of = pd.Timestamp(as_of)
    span = (as_of - obs["issue_date"].min()).days
    origins = min(origins, (span - horizon - min_history_days) // step + 1)
    if origins < 1:
        return None
    full = obs.assign(true_paid_date=obs["paid_date"])
    return backtest_collections(full, as_of, horizon, origins, step)


def demo(seed: int = 7, as_of: str = "2026-10-01", **kwargs) -> dict:
    from .synthetic import generate
    full = generate(seed=seed, as_of=as_of)
    obs = observe(full, as_of)
    opening, outflows = cash_plan(obs, as_of)
    return forecast(obs, as_of, opening, outflows, **kwargs) | {"full": full}
