"""Tahmin değerlendirmesinde uluslararası kabul görmüş testler.

Projede kabul eşikleri kendimiz tarafından belirlenmez; aşağıdaki kurum ve yöntemlerden alınır:

- Basel Bankacılık Denetim Komitesi (BIS), "Supervisory framework for the use of 'backtesting' in
  conjunction with the internal models approach to market risk capital requirements", Ocak 1996
  (BCBS 22). Tahmin aralığının riskli ucunun aşılma sayısı binom dağılımıyla değerlendirilir: doğru bir
  model altında "bu kadar ya da daha az aşım" olasılığı %95'e ulaşıyorsa sarı, %99,99'a ulaşıyorsa
  kırmızı bölge. Sınırlar her örneklem büyüklüğü için yeniden hesaplanır; belge başka güven
  düzeylerinin de sınanabileceğini belirtir. Kasada riskli uç alt uçtur (kötümser senaryonun altı).
  Kapsam sınırı: Basel çerçevesi %99 düzeyinde günlük riske maruz değer ve 250 bağımsız gözlem için kurulmuştur
  (güncel metin: Basel Çerçevesi MAR32.5 ve MAR99.11). Burada aynı bölge kuralı %10 kuyruk olasılığına ve küçük
  örneklemlere uyarlanır; sonuç uyarlanmış bir kapsama tanılamasıdır, Basel ya da BDDK uygunluğu anlamına gelmez.
  Üst üste binen ufuklarda bağımsızlık varsayımı sağlanmaz (bkz. pilot.score, örtüşmeyen alt örneklem).
- Kupiec, P. (1995), "Techniques for verifying the accuracy of risk measurement models", Journal of
  Derivatives 3(2). Aşım oranının beklenen orana eşitliği için olabilirlik oranı testi; iki yönlüdür:
  bant fazla dar da (çok aşım) fazla geniş de (az aşım) olsa reddeder.
- Diebold, F. ve Mariano, R. (1995), "Comparing predictive accuracy", Journal of Business & Economic
  Statistics 13(3); küçük örneklem düzeltmesi Harvey, Leybourne ve Newbold (1997), International
  Journal of Forecasting 13(2). İki tahminin isabeti eşit mi; ufuklar üst üste bindiğinde kayıp farkının
  otokorelasyonu hesaba katılır.

- Spiegelhalter, D. (1986), "Probabilistic prediction in patient management and clinical trials",
  Statistics in Medicine 5(5). Olasılık tahminlerinin (ör. "90 günde eksiye düşme olasılığı %30")
  kalibrasyonu için Brier skoruna dayalı z testi; olasılık tahminlerinde standart doğrulama testidir.

- Dimitriadis, T., Gneiting, T. ve Jordan, A. (2021), "Stable reliability diagrams for probabilistic
  classifiers", PNAS 118(8). CORP: güvenilirlik diyagramı izotonik regresyonla (PAV) kurulur; Brier skoru
  kalibrasyon hatası (MCB), ayırt etme (DSC) ve belirsizlik (UNC) olarak ayrışır: Brier = MCB − DSC + UNC.

- Benjamini, Y. ve Hochberg, Y. (1995), "Controlling the false discovery rate", Journal of the Royal
  Statistical Society B 57(1); pozitif bağımlı testlerde geçerliliği Benjamini ve Yekutieli (2001), Annals
  of Statistics 29(4). Çok sayıda kesit aynı anda sınandığında yalnızca şansla "reddedilen" kesitler ayıklanır.

Tüm testlerde anlamlılık düzeyi %5'tir (bilimsel yayınlarda ve Basel sarı bölge sınırında kullanılan düzey).
"""
from __future__ import annotations

import math

import numpy as np
from scipy import stats

SIGNIFICANCE = 0.05
BASEL_YELLOW = 0.95          # BCBS 1996: P(X <= aşım) >= %95 -> sarı bölge
BASEL_RED = 0.9999           # BCBS 1996: P(X <= aşım) >= %99,99 -> kırmızı bölge


def basel_zone(n: int, exceptions: int, tail_prob: float) -> dict:
    """Basel trafik ışığı. `tail_prob`: doğru modelde bir gözlemin riskli ucu aşma olasılığı (P10 için 0,10).

    Bölge, gözlenen aşım sayısı için P(X <= aşım) binom olasılığına göre belirlenir (BCBS 1996, Tablo 2)."""
    if n <= 0:
        return {"zone": "değerlendirilemedi", "n": n, "exceptions": exceptions, "cum_prob": float("nan")}
    cum = float(stats.binom.cdf(exceptions, n, tail_prob))
    zone = "kırmızı" if cum >= BASEL_RED else ("sarı" if cum >= BASEL_YELLOW else "yeşil")
    yellow_from = int(stats.binom.ppf(BASEL_YELLOW, n, tail_prob))
    # ppf, P(X <= k) >= %95 olan en küçük k'yı verir; sarı bölge o k'dan başlar.
    red_from = int(stats.binom.ppf(BASEL_RED, n, tail_prob))
    return {"zone": zone, "n": int(n), "exceptions": int(exceptions), "expected": n * tail_prob,
            "cum_prob": cum, "yellow_from": yellow_from, "red_from": red_from}


def kupiec_pof(n: int, exceptions: int, rate: float) -> dict:
    """Kupiec (1995) olabilirlik oranı testi: aşım oranı beklenen `rate`e eşit mi (iki yönlü).

    p değeri kesin hesaplanır: doğru modelde aşım sayısı Binom(n, rate) dağılır; LR istatistiğinin bu dağılım
    altında gözlenen değere eşit ya da büyük olma olasılığı toplanır. Asimptotik ki-kare yaklaşımı küçük
    örneklemde ve uç kapsama düzeylerinde ciddi boyut sapması yapar (Kaszyński, Kamiński ve Pankratz;
    ExactVaRTest); küçük işletmenin az sayıdaki kaydında kesin p değeri esastır. Ki-kare p değeri de verilir."""
    if n <= 0:
        return {"lr": float("nan"), "p_value": float("nan"), "reject": None, "observed_rate": float("nan")}
    x = int(exceptions)

    def lr_of(k: np.ndarray) -> np.ndarray:
        k = np.asarray(k, float)
        ph = k / n
        with np.errstate(divide="ignore", invalid="ignore"):
            l0 = (n - k) * np.log(1 - rate) + k * np.log(rate)
            l1 = np.where(k > 0, k * np.log(np.where(k > 0, ph, 1)), 0) + np.where(k < n, (n - k) * np.log(np.where(k < n, 1 - ph, 1)), 0)
        return np.maximum(-2 * (l0 - l1), 0.0)

    lr = float(lr_of(np.array([x]))[0])
    support = np.arange(n + 1)
    exact = float(stats.binom.pmf(support, n, rate)[lr_of(support) >= lr - 1e-9].sum())
    return {"lr": lr, "p_value": min(exact, 1.0), "p_value_chi2": float(stats.chi2.sf(lr, 1)),
            "reject": bool(exact < SIGNIFICANCE), "observed_rate": x / n, "expected_rate": rate, "n": int(n),
            "exceptions": x}


def diebold_mariano(loss_model, loss_bench, overlap: int = 1) -> dict:
    """Diebold-Mariano testi, Harvey-Leybourne-Newbold küçük örneklem düzeltmesiyle.

    `loss_*`: aynı tahmin tarihlerindeki kayıplar (ör. mutlak hata). `overlap`: ardışık tahminlerin ufuklarının
    kaç adım üst üste bindiği (h); kayıp farkının h-1 gecikmeye kadar otokorelasyonu varyansa katılır.
    Dönen `p_worse`: "model kıyastan kötü değildir" sıfır hipotezine karşı modelin daha kötü olduğuna dair tek
    yönlü p değeri; `p_better` tersi. Anlamlılık %5."""
    d = np.asarray(loss_model, float) - np.asarray(loss_bench, float)
    d = d[np.isfinite(d)]
    T, h = len(d), max(int(overlap), 1)
    if T < 4:
        return {"stat": float("nan"), "p_worse": float("nan"), "p_better": float("nan"), "n": T,
                "mean_diff": float(d.mean()) if T else float("nan")}
    dbar = d.mean()
    gamma = [np.mean((d[k:] - dbar) * (d[:T - k] - dbar)) for k in range(h)]
    var = (gamma[0] + 2 * sum(gamma[1:])) / T
    if var <= 0:                                      # küçük örneklemde olabilir (Harvey vd. 2017): yalnız gamma0
        var = gamma[0] / T
    if var <= 0:
        return {"stat": float("nan"), "p_worse": float("nan"), "p_better": float("nan"), "n": T,
                "mean_diff": float(dbar)}
    dm = dbar / math.sqrt(var)
    hln = dm * math.sqrt(max((T + 1 - 2 * h + h * (h - 1) / T) / T, 1e-12))
    return {"stat": float(hln), "p_worse": float(stats.t.sf(hln, T - 1)), "p_better": float(stats.t.cdf(hln, T - 1)),
            "n": T, "mean_diff": float(dbar)}


def random_effects(estimates, std_errors, level: float = 0.95) -> dict:
    """Rastgele etkiler meta-analizi: DerSimonian-Laird heterojenlik (tau²), Hartung-Knapp-Sidik-Jonkman (HKSJ)
    güven aralığı (t dağılımı, k-1 serbestlik derecesi). Az çalışmada HKSJ, gözlenen heterojenlik düşükken aralığı
    fazla daraltabildiği için ölçek katsayısı en az 1 alınır (Röver, Knapp ve Friede 2015, BMC Medical Research
    Methodology 15:99). Cochrane El Kitabı bölüm 10.10.4: HKSJ az çalışmada Wald tipi aralıktan iyidir; iki üç
    çalışmada aralık çok geniş çıkabilir. Tek çalışmada birleştirme yapılmaz, o çalışmanın normal aralığı döner."""
    y, se = np.asarray(estimates, float), np.asarray(std_errors, float)
    ok = np.isfinite(y) & np.isfinite(se) & (se > 0)
    y, se = y[ok], se[ok]
    k = len(y)
    if k == 0:
        return {"k": 0, "estimate": float("nan"), "ci": None, "tau2": float("nan")}
    z = stats.norm.ppf(0.5 + level / 2)
    if k == 1:
        return {"k": 1, "estimate": float(y[0]), "ci": (float(y[0] - z * se[0]), float(y[0] + z * se[0])), "tau2": 0.0}
    w = 1 / se ** 2
    fixed = np.sum(w * y) / np.sum(w)
    q = np.sum(w * (y - fixed) ** 2)
    tau2 = max(0.0, (q - (k - 1)) / (np.sum(w) - np.sum(w ** 2) / np.sum(w)))
    ws = 1 / (se ** 2 + tau2)
    mu = np.sum(ws * y) / np.sum(ws)
    scale = max(1.0, np.sum(ws * (y - mu) ** 2) / (k - 1))
    half = stats.t.ppf(0.5 + level / 2, k - 1) * math.sqrt(scale / np.sum(ws))
    return {"k": k, "estimate": float(mu), "ci": (float(mu - half), float(mu + half)), "tau2": float(tau2)}


def interval_report(actual, lo, hi, tail_prob: float = 0.10) -> dict:
    """P10–P90 aralığı için standart değerlendirme: alt uçta Basel bölgesi ve Kupiec, üst uçta Kupiec,
    merkezi %80 aralık için Kupiec."""
    actual, lo, hi = (np.asarray(v, float) for v in (actual, lo, hi))
    n = len(actual)
    below, above = int((actual < lo).sum()), int((actual > hi).sum())
    return {"n": n, "below": below, "above": above,
            "basel_lower": basel_zone(n, below, tail_prob),
            "kupiec_lower": kupiec_pof(n, below, tail_prob),
            "kupiec_upper": kupiec_pof(n, above, tail_prob),
            "kupiec_central": kupiec_pof(n, below + above, 2 * tail_prob)}


def passes(report: dict) -> bool:
    """Aralık standartları sağlanıyor mu: alt uç Basel yeşil ve hiçbir Kupiec testi reddetmiyor."""
    return (report["basel_lower"]["zone"] == "yeşil" and not report["kupiec_lower"]["reject"]
            and not report["kupiec_upper"]["reject"] and not report["kupiec_central"]["reject"])


def spiegelhalter(prob, outcome) -> dict:
    """Spiegelhalter (1986) kalibrasyon z testi ve Brier skoru. `prob`: tahmin edilen olasılıklar,
    `outcome`: 0/1 gerçekleşme. p < 0,05 ise olasılıklar kalibre değildir (sistematik iyimser ya da kötümser)."""
    p, y = np.clip(np.asarray(prob, float), 1e-9, 1 - 1e-9), np.asarray(outcome, float)
    brier = float(np.mean((y - p) ** 2))
    num = np.sum((y - p) * (1 - 2 * p))
    den = math.sqrt(np.sum((1 - 2 * p) ** 2 * p * (1 - p)))
    if den == 0:
        return {"brier": brier, "z": float("nan"), "p_value": float("nan"), "reject": None, "n": len(p)}
    z = float(num / den)
    pv = float(2 * stats.norm.sf(abs(z)))
    return {"brier": brier, "z": z, "p_value": pv, "reject": bool(pv < SIGNIFICANCE), "n": len(p),
            "mean_prob": float(p.mean()), "observed": float(y.mean())}


def corp(prob, outcome) -> dict:
    """CORP güvenilirlik analizi ve Brier ayrıştırması (Dimitriadis, Gneiting ve Jordan 2021).

    PAV ile yeniden ayarlanmış olasılıklar, tahminin "doğru ayarlı olsaydı" hâlidir. MCB (miscalibration):
    yeniden ayarla kazanılabilecek Brier; DSC (discrimination): ayırt etme gücü; UNC: olayın kendi belirsizliği.
    `curve`, diyagram için (tahmin, yeniden ayarlı) çiftleridir."""
    from sklearn.isotonic import IsotonicRegression
    p, y = np.asarray(prob, float), np.asarray(outcome, float)
    rec = IsotonicRegression(y_min=0.0, y_max=1.0, increasing=True, out_of_bounds="clip").fit_transform(p, y)
    brier = lambda q: float(np.mean((y - q) ** 2))
    s, s_c, s_r = brier(p), brier(rec), brier(np.full_like(y, y.mean()))
    order = np.argsort(p)
    return {"brier": s, "mcb": s - s_c, "dsc": s_r - s_c, "unc": s_r,
            "curve": list(zip(p[order].round(4).tolist(), rec[order].round(4).tolist()))}


def benjamini_hochberg(p_values) -> np.ndarray:
    """Benjamini-Hochberg düzeltilmiş p değerleri (q değerleri); q < %5 olan bulgularda yanlış keşif oranı
    en çok %5'tir. NaN değerler NaN kalır."""
    p = np.asarray(p_values, float)
    out = np.full_like(p, np.nan)
    ok = ~np.isnan(p)
    m = int(ok.sum())
    if not m:
        return out
    order = np.argsort(p[ok])
    ranked = p[ok][order] * m / np.arange(1, m + 1)
    q = np.minimum.accumulate(ranked[::-1])[::-1].clip(max=1.0)
    res = np.empty(m)
    res[order] = q
    out[ok] = res
    return out
