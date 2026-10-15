"""Tahmin değerlendirmesinde uluslararası kabul görmüş testler.

Projede kabul eşikleri kendimiz tarafından belirlenmez; aşağıdaki kurum ve yöntemlerden alınır:

- Basel Bankacılık Denetim Komitesi (BIS), "Supervisory framework for the use of 'backtesting' in
  conjunction with the internal models approach to market risk capital requirements", Ocak 1996
  (BCBS 22). Tahmin aralığının riskli ucunun aşılma sayısı binom dağılımıyla değerlendirilir: doğru bir
  model altında "bu kadar ya da daha az aşım" olasılığı %95'e ulaşıyorsa sarı, %99,99'a ulaşıyorsa
  kırmızı bölge. Sınırlar her örneklem büyüklüğü için yeniden hesaplanır; belge başka güven
  düzeylerinin de sınanabileceğini belirtir. Kasada riskli uç alt uçtur (kötümser senaryonun altı).
- Kupiec, P. (1995), "Techniques for verifying the accuracy of risk measurement models", Journal of
  Derivatives 3(2). Aşım oranının beklenen orana eşitliği için olabilirlik oranı testi; iki yönlüdür:
  bant fazla dar da (çok aşım) fazla geniş de (az aşım) olsa reddeder.
- Diebold, F. ve Mariano, R. (1995), "Comparing predictive accuracy", Journal of Business & Economic
  Statistics 13(3); küçük örneklem düzeltmesi Harvey, Leybourne ve Newbold (1997), International
  Journal of Forecasting 13(2). İki tahminin isabeti eşit mi; ufuklar üst üste bindiğinde kayıp farkının
  otokorelasyonu hesaba katılır.

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
    """Kupiec (1995) olabilirlik oranı testi: aşım oranı beklenen `rate`e eşit mi (iki yönlü)."""
    if n <= 0:
        return {"lr": float("nan"), "p_value": float("nan"), "reject": None, "observed_rate": float("nan")}
    x = int(exceptions)
    phat = x / n

    def loglik(p: float) -> float:
        p = min(max(p, 1e-12), 1 - 1e-12)
        return (n - x) * math.log(1 - p) + x * math.log(p)

    lr = -2 * (loglik(rate) - (loglik(phat) if 0 < x < n else (n * math.log(1 - 1e-12) if x == 0 else 0.0)))
    lr = max(lr, 0.0)
    p_value = float(stats.chi2.sf(lr, 1))
    return {"lr": float(lr), "p_value": p_value, "reject": bool(p_value < SIGNIFICANCE),
            "observed_rate": phat, "expected_rate": rate, "n": int(n), "exceptions": x}


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
