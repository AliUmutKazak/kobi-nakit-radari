"""Pilot raporu: bir işletme için tek sayfalık, yazdırılabilir HTML.

İçerik ve ölçütler docs/pilot/PILOT_PROTOKOLU.md'de önceden tanımlanmıştır; rapor yalnızca onları
hesaplar. Hiçbir dış kaynağa bağlanmaz (grafik, sayfanın içine çizilen SVG'dir).
"""
from __future__ import annotations

import html
import json

import numpy as np
import pandas as pd

from . import actions
from .anonymize import invoice_aliases, pseudonym
from .open_data import delay_study
from .synthetic import observe
from .pipeline import forecast, gap_summary, naive_collections, payments_cutoff, weekly_table
from .reconcile import collection_events
from .standards import (SIGNIFICANCE, basel_zone, diebold_mariano, interval_report, kupiec_pof,
                        passes as interval_passes, random_effects)

VERSION = "2026.10.21"            # tahmin kaydına yazılır: hangi kod sürümüyle üretildiği
MIN_HISTORY_DAYS = 365            # protokol 2. bölüm: en az 12 aylık fatura geçmişi; altında geri test yapılmaz
# Aşama 0 (protokol 1.6): ileriye dönük pilotla aynı tanım, geçmişe uygulanmış hâli. Kayan başlangıç noktalı
# değerlendirme (rolling origin; Tashman 2000, International Journal of Forecasting 16): haftada bir tahmin günü,
# her biri yalnızca o güne kadarki veriyle; en fazla son 52 hafta; her tahmin gününden önce en az 180 günlük geçmiş.
RETRO_STEP = 7
RETRO_MAX_ORIGINS = 52
RETRO_MIN_TRAIN_DAYS = 180
RETRO_MIN_ORIGINS = 4              # Diebold-Mariano testi için en az kayıt (accuracy_test)
MIN_MATCH_RATE = 0.80             # banka tahsilatlarının bu oranın altında eşleştiği kayıt uyarılıdır, B1'e girmez
ALPHA = 0.2                       # P10–P90 aralığı: %80 merkezi aralık


def _interval_score(lo, hi, y):
    """Gneiting ve Raftery (2007) aralık skoru, alfa = 0,2: aralık genişliği + dışarıda kalma cezası (düşük iyi)."""
    lo, hi, y = (np.asarray(v, float) for v in (lo, hi, y))
    return (hi - lo) + 2 / ALPHA * np.maximum(lo - y, 0) + 2 / ALPHA * np.maximum(y - hi, 0)


def _tl(x) -> str:
    return f"{float(x):,.0f}".replace(",", ".") + " TL"


def _pct(x) -> str:
    return f"%{float(x) * 100:.0f}"


def _table(df: pd.DataFrame) -> str:
    head = "".join(f"<th>{html.escape(str(c))}</th>" for c in df.columns)
    body = "".join("<tr>" + "".join(f"<td>{html.escape(str(v))}</td>" for v in row) + "</tr>"
                   for row in df.itertuples(index=False))
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def _band_svg(sim, width: int = 720, height: int = 220) -> str:
    """Kasa bandı (P10–P90) ve orta tahmin (P50) çizgisi; sıfır çizgisi kesikli."""
    lo, mid, hi = sim.p10, sim.p50, sim.p90
    ymin, ymax = min(lo.min(), 0.0), max(hi.max(), 0.0)
    span = (ymax - ymin) or 1.0
    x = lambda i: 40 + i * (width - 50) / (len(mid) - 1)
    y = lambda v: 10 + (ymax - v) * (height - 30) / span
    band = " ".join(f"{x(i):.1f},{y(v):.1f}" for i, v in enumerate(hi)) + " " + \
        " ".join(f"{x(i):.1f},{y(v):.1f}" for i, v in reversed(list(enumerate(lo))))
    line = " ".join(f"{x(i):.1f},{y(v):.1f}" for i, v in enumerate(mid))
    ticks = "".join(f'<text x="{x(d):.0f}" y="{height - 4}" class="t">{(sim.dates[d]):%d.%m}</text>'
                    for d in range(0, len(mid), 14))
    return (f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="90 günlük kasa bandı">'
            f'<polygon points="{band}" class="band"/><polyline points="{line}" class="mid"/>'
            f'<line x1="40" x2="{width - 10}" y1="{y(0):.1f}" y2="{y(0):.1f}" class="zero"/>'
            f'<text x="2" y="{y(ymax) + 4:.0f}" class="t">{ymax / 1e6:.1f} mn</text>'
            f'<text x="2" y="{y(0) + 4:.0f}" class="t">0</text>{ticks}</svg>')


def build(obs: pd.DataFrame, as_of, opening: float = 0.0, outflows: pd.DataFrame | None = None,
          label: str = "İşletme", cheques: pd.DataFrame | None = None, unmatched: pd.DataFrame | None = None,
          n_payments: int | None = None, res: dict | None = None, key: str | None = None,
          retro: pd.DataFrame | None = None) -> dict:
    """Raporun bütün sayılarını hesaplar (HTML'den bağımsız; testlerde de kullanılır).

    `res` verilirse (panelde zaten hesaplanmış tahmin) kasa yeniden simüle edilmez. `key` verilirse
    öncelik listesindeki müşteri adları takma adlarla değiştirilir (rapor paylaşılacaksa)."""
    as_of = pd.Timestamp(as_of)
    if res is None:
        flows = outflows if outflows is not None else pd.DataFrame({"date": [], "amount": []})
        res = forecast(obs, as_of, opening, flows, cheques=cheques, payments_through=payments_cutoff(obs, as_of))
    conc = actions.concentration(obs)
    last = max(obs["issue_date"].max(), obs["paid_date"].max() if obs["paid_date"].notna().any() else obs["issue_date"].max())
    quality = {
        "Fatura sayısı": len(obs), "Müşteri sayısı": int(obs["customer_id"].nunique()),
        "Veri dönemi": f"{obs['issue_date'].min():%d.%m.%Y} – {obs['issue_date'].max():%d.%m.%Y}",
        "Son hareket": f"{last:%d.%m.%Y} ({(as_of - last).days} gün önce)",
        "Ödenmiş fatura": f"{obs['paid_date'].notna().mean() * 100:.0f}%",
        "Açık alacağın üç büyük müşteri payı": _pct(conc["top_share"]),
    }
    if n_payments:
        quality["Banka tahsilatlarının faturalarla eşleşme oranı"] = _pct(1 - (len(unmatched) if unmatched is not None else 0) / n_payments)
    history_days = (obs["issue_date"].max() - obs["issue_date"].min()).days
    delays = delay_study(obs, origins=4, step=60) if history_days >= MIN_HISTORY_DAYS else pd.DataFrame()
    # Veri tahmin tarihinden eskiyse, son hareketten sonraki ödemeler bilinmez; geri test orada biter.
    if retro is not None and len(retro):          # Aşama 0 yapılmışsa kısa geri testin yerine o raporlanır
        cash = retro
    else:
        cash = cash_backtest(obs, min(as_of, last)) if history_days >= MIN_HISTORY_DAYS else pd.DataFrame()
    return {"label": label, "as_of": as_of, "res": res, "quality": quality, "delays": delays, "cash": cash,
            "retro": retro is not None and len(retro) > 0,
            "gap": gap_summary(res), "weeks": weekly_table(res), "top": _top(res, key, obs),
            "record": forward_record(obs, as_of, events=res.get("events") if isinstance(res, dict) else None,
                                     payments_through=res["info"].get("payments_through")), "cash_record": cash_record(res)}


SIMPLE_METHODS = {"medyan": ("naive_median", "müşteri her zamanki kadar geç öder"),
                  "oran": ("naive_rate", "son dönemin tahsilat oranı sürer"),
                  "vade": ("naive_due", "her fatura vadesinde ödenir")}


def simple_replacements(retro: pd.DataFrame, obs: pd.DataFrame, as_of) -> list[dict]:
    """Aşama 0'da modelin "geride" kaldığı her ufuk için, o işletmenin geçmişinde en isabetli çıkan basit yöntemle
    bugün açık faturalardan beklenen tahsilat (protokol 1.6). Basit yöntemlerin bandı yoktur; bu yüzden kasa bandı
    yerine geçmez, o ufuktaki tahsilat sayısı olarak gösterilir."""
    if retro is None or not len(retro) or "dm_sonuc" not in retro:
        return []
    as_of = pd.Timestamp(as_of)
    book = obs[(obs["issue_date"] <= as_of) & ~(obs["paid_date"] <= as_of) & (obs["open_amount"] > 0)]
    book = book.assign(amount=book["open_amount"])
    out = []
    for _, row in retro[retro["dm_sonuc"] == "geride"].iterrows():
        errs = {m: row.get(f"sapma_{m}_%") for m in SIMPLE_METHODS if pd.notna(row.get(f"sapma_{m}_%"))}
        if not errs:
            continue
        best = min(errs, key=errs.get)
        h = int(row["ufuk_gun"])
        value = naive_collections(obs, book, as_of, as_of + pd.Timedelta(days=h))[SIMPLE_METHODS[best][0]]
        out.append({"ufuk_gun": h, "yontem": best, "ad": SIMPLE_METHODS[best][1], "tutar": value,
                    "sapma_model": float(row["sapma_model_%"]), "sapma_yontem": float(errs[best])})
    return out


def data_end(obs: pd.DataFrame, as_of) -> pd.Timestamp:
    """Verideki son hareket (tahmin tarihinden sonrası sayılmaz): geri testin ufukları bu günden önce biter."""
    last = max(obs["issue_date"].max(), obs["paid_date"].max() if obs["paid_date"].notna().any() else obs["issue_date"].max())
    return min(pd.Timestamp(as_of), last)


def retro_origins(obs: pd.DataFrame, as_of, horizons=(14, 30)) -> int:
    """Aşama 0'da kaç haftalık tahmin günü kurulabilir (0: yetersiz geçmiş)."""
    span = (data_end(obs, as_of) - obs["issue_date"].min()).days - max(horizons) - RETRO_MIN_TRAIN_DAYS
    return int(max(0, min(RETRO_MAX_ORIGINS, span // RETRO_STEP + 1)))


def retrospective(obs: pd.DataFrame, as_of, progress=None, events: pd.DataFrame | None = None) -> pd.DataFrame | None:
    """Aşama 0: geriye dönük pilot testi. Sonuç, ileriye dönük B1/B2 ile aynı ölçütlerle (Diebold-Mariano,
    Basel trafik ışığı, Kupiec) ufuk başına özet tablodur; yeterli geçmiş yoksa None. Haftalık tahmin günlerinin
    ufukları üst üste biner: Diebold-Mariano bunu hesaba katar, Basel ve Kupiec katmaz (ileriye dönük pilottaki
    haftalık kayıtlarla aynı); bu yüzden sonuç B1/B2 kararının yerine geçmez."""
    n = retro_origins(obs, as_of)
    if n < RETRO_MIN_ORIGINS:
        return None
    return cash_backtest(obs, data_end(obs, as_of), origins=n, step=RETRO_STEP, progress=progress, events=events)


def cash_backtest(obs: pd.DataFrame, as_of, horizons=(14, 30), origins: int = 4, step: int = 21,
                  n_sims: int = 500, progress=None, events: pd.DataFrame | None = None,
                  same_as_forward: bool = True, raw: bool = False) -> pd.DataFrame:
    """Kasa düzeyinde geri test: geçmiş tarihlerde, o gün açık faturalardan 14 ve 30 günde tahsil edilen tutar.

    Her tahmin tarihinde tek simülasyondan iki ufuk birden okunur (açılış sıfır, gider ve yeni satış yokken kasa
    yolu birikmiş tahsilattır). Her ufuk veri kesiminden (as_of) önce biter. Sapmanın yanında bandın ortalama
    genişliği ve aralık skoru da verilir: yalnızca "bant içinde kaldı mı" sorusu, gereksiz geniş bandı ödüllendirir.

    same_as_forward=True (varsayılan): tanım ileriye dönük kayıtla (forward_record) ve puanlamayla (score) aynıdır.
    Çekle kapanan fatura kapanış gününde sayılır (çek ayarı kapalı); tahmin günü açık tutar ve taksit alışkanlığı
    o güne kadarki tahsilat olaylarından gelir; kayıtlar tahmin gününe kadar işlenmiş sayılır; gerçekleşen,
    tahmin gününden sonraki tahsilat olaylarının toplamıdır (kısmi ödemeler kendi tarihiyle). Dış inceleme
    (21.10.2026) eski tanımın farklı olduğunu buldu: çekli işletmede model haksız yere "geride" çıkabiliyordu.
    False yalnızca eski tanımla karşılaştırma içindir. raw=True: özet yerine tahmin günü satırları."""
    as_of, H = pd.Timestamp(as_of), max(horizons)
    full = obs.assign(true_paid_date=obs["paid_date"])
    ev = collection_events(obs) if events is None else events
    ev = ev.assign(issue=ev["invoice_id"].astype(str).map(obs.set_index(obs["invoice_id"].astype(str))["issue_date"]))
    rows = []
    for k in range(origins):
        t = as_of - pd.Timedelta(days=H + k * step)
        past = observe(full, t)
        was_open = (full["issue_date"] <= t) & ~(full["true_paid_date"] <= t)
        if same_as_forward:
            ev_t = ev[ev["date"] <= t]
            paid_by_t = ev_t.groupby(ev_t["invoice_id"].astype(str))["amount"].sum()
            # Tahmin günü açık tutar: fatura tutarı eksi o güne kadarki tahsilat olayları (kısmi ödemeler).
            open_t = (past["amount"] - past["invoice_id"].astype(str).map(paid_by_t).fillna(0.0)).clip(lower=0.0)
            past["open_amount"] = np.where(past["paid_date"].isna(), open_t, 0.0)
            sim = forecast(past, t, 0.0, pd.DataFrame({"date": [], "amount": []}), H, n_sims,
                           include_projected=False, seed=k, cheque_aware=False, events=ev_t,
                           payments_through=t)["sim"]
            book = past[(past["paid_date"].isna()) & (past["open_amount"] > 0)]
            book = book.assign(amount=book["open_amount"])
        else:
            sim = forecast(past, t, 0.0, pd.DataFrame({"date": [], "amount": []}), H, n_sims,
                           include_projected=False, seed=k)["sim"]
            book = full[was_open]
        for h in horizons:
            end = t + pd.Timedelta(days=h)
            if same_as_forward:
                actual = ev.loc[(ev["issue"] <= t) & (ev["date"] > t) & (ev["date"] <= end), "amount"].sum()
            else:
                actual = full.loc[was_open & (full["true_paid_date"] <= end), "amount"].sum()
            rows.append({"h": h, "origin": t, "actual": float(actual),
                         "p10": sim.p10[h], "p50": sim.p50[h], "p90": sim.p90[h],
                         **naive_collections(past, book, t, end)})
        if progress is not None:
            progress((k + 1) / origins)
    bt = pd.DataFrame(rows)
    return bt if raw else summarize_backtest(bt, step)


# Protokol 1.7: B1 eşdeğerlik (non-inferiority) iddiasıdır; kabul marjı önceden belirlenir (FDA 2016, "Non-Inferiority
# Clinical Trials to Establish Effectiveness"; CONSORT uzantısı, Piaggio vd. 2012). M1: kontrol yönteminin (en iyi
# güçlü basit yöntem) plaseboya ("vadesinde öder", KOBİ'nin fiilen yaptığı varsayım) karşı geçmişte gösterilmiş
# üstünlüğü; ihtiyatlı olsun diye %95 güven aralığının alt sınırı. M2 = M1'in %50'si (FDA: kardiyovasküler sonuç
# çalışmalarında yerleşik uygulama, "etkinin en az yarısını korumak"). Karar: model eksi en iyi basit yöntem farkının
# iki yönlü %95 güven aralığının üst sınırı M2'den küçükse eşdeğer (FDA: tek yönlü alfa 0,025).
MARGIN_FRACTION = 0.5
CI_LEVEL = 95


def _err(d: pd.DataFrame, col: str, actual: str) -> float:
    total = d[actual].abs().sum()
    return (d[col] - d[actual]).abs().sum() / total * 100 if total else float("nan")


def block_bootstrap(g: pd.DataFrame, date_col: str, block: int, stat, n_boot: int = 1000, seed: int = 0) -> np.ndarray:
    """Tarih blokları yeniden örneklenerek bir istatistiğin dağılımı: üst üste binen ufuklarda ardışık kayıtlar
    birlikte örneklenir (hareketli blok bootstrap; Künsch 1989)."""
    rng = np.random.default_rng(seed)
    dates = sorted(g[date_col].unique())
    by_date = {x: g[g[date_col] == x] for x in dates}
    out = []
    for _ in range(n_boot):
        starts = rng.integers(0, len(dates), int(np.ceil(len(dates) / block)))
        pick = [dates[(st + j) % len(dates)] for st in starts for j in range(block)][:len(dates)]
        out.append(stat(pd.concat([by_date[x] for x in pick])))
    return np.asarray(out)


def ci(values: np.ndarray, level: int = CI_LEVEL) -> tuple[float, float]:
    tail = (100 - level) / 2
    return float(np.percentile(values, tail)), float(np.percentile(values, 100 - tail))


def b1_margin(g: pd.DataFrame, h: int, step: int, actual: str = "actual", cols=None, date_col: str = "origin",
              seed: int = 0) -> dict:
    """Aşama 0 satırlarından B1 kabul marjı (M1, M2; sapma puanı). M1 ≤ 0 ise kontrolün etkisi gösterilemedi:
    marj belirlenemez ve B1 yalnızca üstünlükle geçer."""
    cols = cols or {"vade": "naive_due", "medyan": "naive_median", "oran": "naive_rate"}
    strong = [m for m in ("medyan", "oran") if g[cols[m]].notna().all()]
    if not strong or len(g[date_col].unique()) < RETRO_MIN_ORIGINS:
        return {"m1": None, "m2": None}
    best = min(strong, key=lambda m: _err(g, cols[m], actual))
    diffs = block_bootstrap(g, date_col, max(1, int(np.ceil(h / step))),
                            lambda d: _err(d, cols["vade"], actual) - _err(d, cols[best], actual), seed=seed)
    m1 = ci(diffs)[0]
    point = _err(g, cols["vade"], actual) - _err(g, cols[best], actual)
    return {"m1": m1, "m2": MARGIN_FRACTION * m1 if m1 > 0 else None, "kontrol": best,
            "m1_tahmin": float(point), "m1_se": float(np.std(diffs, ddof=1))}


def b1_decision(ci95: tuple[float, float] | None, m2: float | None, worse_than_due: bool) -> tuple[bool | None, str]:
    """Protokol 1.7 B1 kararı: (geçti mi, sonuç)."""
    if ci95 is None:
        return None, "değerlendirilemedi (az kayıt)"
    lo, hi = ci95
    if worse_than_due:
        return False, "geride (vadesinde öder'den kötü)"
    if hi < 0:
        return True, "üstün"
    if m2 is not None and hi < m2:
        return True, "eşdeğer (marj içinde)"
    if m2 is not None and lo > m2:
        return False, "geride (marjın dışında)"
    return False, "kanıtlanamadı" + ("" if m2 is not None else " (marj belirlenemedi)")


def pooled_b1(firms: pd.DataFrame) -> pd.DataFrame:
    """Protokol 1.8 birincil karar: bütün pilot işletmelerinin birleşik analizi (ufuk başına).

    `firms`: işletme ve ufuk başına bir satır; sütunlar ufuk_gun, fark_tahmin, fark_se (ileriye dönük pilottan,
    model eksi en iyi güçlü basit yöntem, sapma puanı) ve m1_tahmin, m1_se (o işletmenin Aşama 0'ından, en iyi
    basit yöntemin "vadesinde öder"e üstünlüğü). Fark ve M1 ayrı ayrı rastgele etkiler meta-analiziyle birleştirilir
    (standards.random_effects). Birleşik M2 = birleşik M1'in %95 alt sınırının yarısı (FDA 2016, protokol 1.7).
    Karar b1_decision ile verilir. İşletme başına sonuçlar betimleyicidir: Cochrane El Kitabı (12.2.2.1), istatistiksel
    anlamlılığa dayalı oy sayımını "ciddi sınırlılıkları olan ve yanlış sonuca götürebilen", kabul edilemez bir
    yöntem sayar."""
    out = []
    for h, g in firms.groupby("ufuk_gun"):
        usable = g["fark_tahmin"].notna() & g["fark_se"].gt(0)
        diff = random_effects(g["fark_tahmin"], g["fark_se"])
        m1 = random_effects(g["m1_tahmin"], g["m1_se"]) if {"m1_tahmin", "m1_se"} <= set(g) else {"ci": None}
        m1_lo = m1["ci"][0] if m1.get("ci") else None
        m2 = MARGIN_FRACTION * m1_lo if m1_lo is not None and m1_lo > 0 else None
        passed, result = b1_decision(diff["ci"], m2, False)
        row = {"ufuk_gun": int(h), "isletme": diff["k"], "yetersiz_kayitli_isletme": int((~usable).sum()),
               "fark_birlesik": diff["estimate"],
               "fark_ci95": diff["ci"], "tau2": diff["tau2"], "m1_alt_sinir": m1_lo, "m2": m2,
               "B1": passed, "B1_sonuc": result}
        if {"kayit", "alt_asim", "ust_asim"} <= set(g):           # B2 birleşik: aşımlar toplanır
            n, lo, hi = int(g["kayit"].sum()), int(g["alt_asim"].sum()), int(g["ust_asim"].sum())
            row.update({"B2_kayit": n, "B2_basel_alt": basel_zone(n, lo, 0.10)["zone"],
                        "B2_kupiec_alt_p": kupiec_pof(n, lo, 0.10)["p_value"],
                        "B2_kupiec_ust_p": kupiec_pof(n, hi, 0.10)["p_value"]})
        out.append(row)
    return pd.DataFrame(out)


def package_rows(folder) -> tuple[pd.DataFrame, dict]:
    """Proje tarafı: bir işletmenin açılmış takma adlı pilot paketinden birleşik analiz satırları (ufuk başına) ve o
    işletmenin dondurulmuş marjı. Paket: faturalar.csv (güncel), isteğe bağlı ekstre.csv, pilot_kayitlari.csv,
    asama0.csv, b1_marj.json. Puanlama paneldekiyle aynı koddur (score)."""
    from pathlib import Path

    from .ingest import load_invoices, load_payments
    from .reconcile import reconcile

    folder = Path(folder)
    later, _ = load_invoices(folder / "faturalar.csv")
    if (folder / "ekstre.csv").exists():
        paid, allocations, _ = reconcile(later.assign(open_amount=later["amount"], paid_date=pd.NaT),
                                         load_payments(folder / "ekstre.csv")[0])
        events = collection_events(paid, allocations)
    else:
        events = collection_events(later)
    margins = json.loads((folder / "b1_marj.json").read_text(encoding="utf-8")) if (folder / "b1_marj.json").exists() else {}
    m2 = {int(h): float(v) for h, v in margins.get("m2", {}).items()}
    records = records_from_table(pd.read_csv(folder / "pilot_kayitlari.csv"))
    _, summary = score(records, later, events=events, margins=m2)
    rows = summary[summary["hedef"] == "tahsilat"] if len(summary) else summary
    out = pd.DataFrame({"isletme": folder.name, "ufuk_gun": rows.get("ufuk_gun", []),
                        "fark_tahmin": rows.get("fark_tahmin", []), "fark_se": rows.get("fark_se", []),
                        "kayit": rows.get("kayit", []), "alt_asim": rows.get("alt_asim", []),
                        "ust_asim": rows.get("ust_asim", [])})
    if (folder / "asama0.csv").exists():
        retro = pd.read_csv(folder / "asama0.csv").set_index("ufuk_gun")
        for col, src in (("m1_tahmin", "b1_m1_tahmin"), ("m1_se", "b1_m1_se")):
            out[col] = out["ufuk_gun"].map(retro[src]) if src in retro else float("nan")
    return out.reset_index(drop=True), margins


def summarize_backtest(bt: pd.DataFrame, step: int) -> pd.DataFrame:
    """Geri test satırlarından (h, actual, p10, p50, p90, naive_*) ufuk başına özet ve standart testler."""
    out = []
    for h, g in bt.groupby("h"):
        total = g["actual"].sum() or float("nan")
        err = lambda col: (g[col] - g["actual"]).abs().sum() / total * 100
        errors = pd.DataFrame({"model": (g["p50"] - g["actual"]).abs(), "vade": (g["naive_due"] - g["actual"]).abs(),
                               "medyan": (g["naive_median"] - g["actual"]).abs(),
                               "oran": (g["naive_rate"] - g["actual"]).abs()})
        acc = accuracy_test(errors, overlap=int(np.ceil(h / step)))
        band = interval_report(g["actual"], g["p10"], g["p90"])
        out.append({"ufuk_gun": h, "tahmin_tarihi_sayisi": len(g), "sapma_model_%": err("p50"),
                    "sapma_medyan_%": err("naive_median"), "sapma_vade_%": err("naive_due"),
                    "sapma_oran_%": err("naive_rate"),
                    "bant_ici": ((g["p10"] <= g["actual"]) & (g["actual"] <= g["p90"])).mean(),
                    "bant_genisligi_%": (g["p90"] - g["p10"]).sum() / total * 100,
                    "aralik_skoru_%": _interval_score(g["p10"], g["p90"], g["actual"]).sum() / total * 100,
                    "dm_sonuc": acc["sonuc"], "dm_kiyas": acc["kiyas"], "B1": acc["B1"],
                    "alt_asim": band["below"], "ust_asim": band["above"],
                    "basel_alt": band["basel_lower"]["zone"], "kupiec_p": band["kupiec_central"]["p_value"],
                    "B2": interval_passes(band),
                    **({f"b1_{k}": v for k, v in b1_margin(g, h, step).items()} if "origin" in g else {})})
    return pd.DataFrame(out)


def forward_record(obs: pd.DataFrame, as_of, horizons=(14, 30), n_sims: int = 1000, events: pd.DataFrame | None = None,
                   payments_through=None) -> pd.DataFrame:
    """İleriye dönük kayıt, hedef A (tahsilat): bugün açık faturalardan önümüzdeki 14 ve 30 günde tahsil
    edilecek tutar; model ve üç basit yöntem. Yeni satışlar, giderler ve açılış kasası bu hedefe dahil değildir.
    Rapor her hafta değiştirilmeden saklanır, ufuk dolunca gerçekleşenle karşılaştırılır (protokol B1).

    Gerçekleşen, tahsilat olaylarından ölçülür (fatura kapanışı ve kısmi tahsilatlar; reconcile.collection_events).
    Tahmin aynı tanımla yapılır: çekle kapanan faturada kapanış günü esas alınır (para çek vadesinde gelse de;
    çek ayarı kapalı), kısmi tahsilatlar olaylardan öğrenilen taksit alışkanlığıyla, tahsilatların işlendiği son gün
    (payments_through) ana tahmindeki gibi. Kasa hedefi (cash_record) ise paranın geldiği günü esas alır."""
    as_of = pd.Timestamp(as_of)
    book = obs[(obs["issue_date"] <= as_of) & ~(obs["paid_date"] <= as_of) & (obs["open_amount"] > 0)]
    book = book.assign(amount=book["open_amount"])
    # Tek simülasyon yeter: açılış kasası sıfır, gider ve yeni satış yokken kasa yolu, o güne kadarki
    # tahsilatın kendisidir; h. günün yüzdelikleri h günlük tahsilatın yüzdelikleridir.
    sim = forecast(obs, as_of, 0.0, pd.DataFrame({"date": [], "amount": []}), horizon=max(horizons), n_sims=n_sims,
                   include_projected=False, cheque_aware=False, events=events, payments_through=payments_through)["sim"]
    rows = []
    for h in horizons:
        end = as_of + pd.Timedelta(days=h)
        lo, mid, hi = sim.p10[h], sim.p50[h], sim.p90[h]
        rows.append({"target": "tahsilat", "horizon": h, "until": f"{end:%Y-%m-%d}",
                     "p10": round(lo), "p50": round(mid), "p90": round(hi),
                     **{k: round(v) if v == v else None for k, v in naive_collections(obs, book, as_of, end).items()}})
    return pd.DataFrame(rows)


def cash_record(res: dict, horizons=(7, 14, 28)) -> pd.DataFrame:
    """İleriye dönük kayıt, hedef B (kapanış kasası): açılış bakiyesinden başlayıp bilinen giderler, borçlar,
    çekler, açık faturalar ve (açıksa) yeni satışlarla 7, 14 ve 28 gün sonraki kasa. Gerçekleşen, o gün
    kullanıcının panele girdiği güncel kasa ve banka toplamıdır. Basit karşılaştırma: "kasa değişmez"."""
    sim, as_of = res["sim"], pd.Timestamp(res["as_of"])
    return pd.DataFrame([{"target": "kasa", "horizon": h, "until": f"{as_of + pd.Timedelta(days=h):%Y-%m-%d}",
                          "p10": round(sim.p10[h]), "p50": round(sim.p50[h]), "p90": round(sim.p90[h]),
                          "naive_flat": round(float(res["opening"]))} for h in horizons if h < len(sim.p50)])


def cash_components(res: dict, horizons=(7, 14, 28)) -> dict:
    """Kasa kaydının kalemleri (AFP: tahmin ile gerçekleşen kalem bazında karşılaştırılır). Ufuk başına beklenen
    (senaryo ortalaması) tutarlar: açık faturalardan ve elde olan çeklerden tahsilat, yeni satışlardan tahsilat,
    planlanan giderler (plan dışı tahmin dahil). Kasa ıskaladığında hatanın hangi kalemden geldiğini gösterir."""
    sim, ctx, as_of = res["sim"], res["ctx"], pd.Timestamp(res["as_of"])
    inv = ctx["sim_inv"]
    amount = inv["open_amount"].to_numpy(float)
    proj = inv["projected"].to_numpy(bool)
    out = res["outflows"]
    out_off = (pd.to_datetime(out["date"]) - as_of).dt.days.to_numpy() if len(out) else np.array([])
    cheques = ctx.get("cheques")
    c_off = (pd.to_datetime(cheques["date"]) - as_of).dt.days.to_numpy() if cheques is not None and len(cheques) else None
    comp = {}
    for h in horizons:
        got = (sim.pay_day <= h).mean(axis=1) * amount
        chq = float(cheques["amount"].to_numpy(float)[(c_off >= 1) & (c_off <= h)].sum()) if c_off is not None else 0.0
        comp[str(h)] = {"acik": round(float(got[~proj].sum()) + chq), "yeni": round(float(got[proj].sum())),
                        "gider": round(float(out["amount"].to_numpy(float)[(out_off >= 1) & (out_off <= h)].sum()) if len(out) else 0.0)}
    return comp


def component_variance(records: pd.DataFrame, obs: pd.DataFrame, events: pd.DataFrame,
                       bank_outflows: pd.DataFrame | None = None) -> pd.DataFrame:
    """Ufku dolmuş kasa kayıtlarında kalem bazında beklenen ile gerçekleşen. Gerçekleşen: açık faturalardan ve
    yeni satışlardan tahsilat olaylardan (fatura kesim gününe göre ayrılır), giderler banka çıkışlarından (yoksa boş)."""
    import json
    if records is None or not len(records):
        return pd.DataFrame()
    rec = records[records["target"] == "kasa"]
    issued = obs.set_index(obs["invoice_id"].astype(str))["issue_date"]
    ev = events.assign(issue=events["invoice_id"].astype(str).map(issued))
    data_end = max(obs["issue_date"].max(), events["date"].max() if len(events) else obs["issue_date"].max())
    rows = []
    for r in rec.itertuples():
        comp = json.loads(r.meta or "{}").get("bilesenler", {}).get(str(int(r.horizon)))
        a, u = pd.Timestamp(r.as_of), pd.Timestamp(r.until)
        if not comp or u > data_end:
            continue
        win = (ev["date"] > a) & (ev["date"] <= u)
        actual = {"acik": float(ev.loc[win & (ev["issue"] <= a), "amount"].sum()),
                  "yeni": float(ev.loc[win & (ev["issue"] > a), "amount"].sum()),
                  "gider": (float(bank_outflows.loc[(bank_outflows["date"] > a) & (bank_outflows["date"] <= u), "amount"].sum())
                            if bank_outflows is not None and len(bank_outflows) else None)}
        for k, label in (("acik", "Açık faturalardan tahsilat"), ("yeni", "Yeni satışlardan tahsilat"), ("gider", "Giderler")):
            rows.append({"hafta": r.as_of, "ufuk": int(r.horizon), "kalem": label, "beklenen": comp[k],
                         "gerceklesen": actual[k],
                         "fark": None if actual[k] is None else actual[k] - comp[k]})
    return pd.DataFrame(rows)


def _top(res: dict, key: str | None, obs: pd.DataFrame) -> pd.DataFrame:
    top = res["ranked"][res["ranked"]["actionable"]].head(10)
    names = top["customer_id"].map(lambda c: pseudonym(key, c)[0]) if key else top["customer_name"]
    # Takma numara, takma adlı paketteki numarayla aynı olsun diye fatura yılı faturanın kendi tarihinden alınır.
    numbers = top["invoice_id"].astype(str).map(invoice_aliases(obs[obs["invoice_id"].isin(top["invoice_id"])], key))         if key else top["invoice_id"]
    top = pd.DataFrame({"Fatura": numbers, "Müşteri": names,
                        "Vade": top["due_date"].dt.strftime("%d.%m.%Y"), "Tutar": top["open_amount"].map(_tl),
                        "Gecikme (gün)": top["days_overdue"], "Risk": top["p_late"].map(_pct)})
    return top


def accuracy_test(errors: pd.DataFrame, overlap: int) -> dict:
    """Ölçüt B1 (standart): Diebold-Mariano testi, Harvey-Leybourne-Newbold düzeltmesiyle, %5 anlamlılık.

    `errors`: tahmin tarihi başına mutlak hatalar (sütunlar: model, vade, medyan, oran). Model, iki güçlü basit
    yöntemden (medyan, oran) toplamda iyi olanla ve "vadesinde öder" ile karşılaştırılır. Sonuç:
    "üstün" (en iyi basit yöntemden anlamlı biçimde iyi), "eşdeğer" (anlamlı fark yok), "geride" (herhangi
    birinden anlamlı biçimde kötü). B1, "geride" değilse geçer. Kendi koyduğumuz bir tolerans yoktur."""
    ok = lambda c: c in errors and errors[c].notna().all() and len(errors) > 0
    strong = [m for m in ("medyan", "oran") if ok(m)]
    if not ok("model") or not strong:
        return {"B1": None, "sonuc": "değerlendirilemedi", "kiyas": None, "p_geride": float("nan"),
                "p_ustun": float("nan")}
    best = min(strong, key=lambda m: errors[m].sum())
    vs_best = diebold_mariano(errors["model"], errors[best], overlap)
    vs_due = diebold_mariano(errors["model"], errors["vade"], overlap) if ok("vade") else {"p_worse": 1.0}
    if not np.isfinite(vs_best["p_worse"]):
        return {"B1": None, "sonuc": "değerlendirilemedi (az kayıt)", "kiyas": best, "p_geride": float("nan"),
                "p_ustun": float("nan")}
    worse = vs_best["p_worse"] < SIGNIFICANCE or vs_due["p_worse"] < SIGNIFICANCE
    better = vs_best["p_better"] < SIGNIFICANCE
    return {"B1": not worse, "sonuc": "geride" if worse else ("üstün" if better else "eşdeğer"), "kiyas": best,
            "p_geride": vs_best["p_worse"], "p_ustun": vs_best["p_better"]}


def verdict(delays: pd.DataFrame, cash: pd.DataFrame) -> str:
    """Rapordaki geri test özeti: Diebold-Mariano sonucu (ölçüt B1) ve sapma yüzdeleri."""
    if cash is None or cash.empty:
        return ("Geri test için yeterli geçmiş yok (en az 12 aylık fatura gerekir); isabet ölçülemedi. "
                "Tahminler bu işletmenin geçmişiyle sınanmadığı için yalnızca yön gösterici okunmalı.")
    if "dm_sonuc" not in cash:
        return "Geri test sonuçları eksik; karşılaştırma değerlendirilemedi."
    results = set(cash["dm_sonuc"])
    if results <= {"değerlendirilemedi", "değerlendirilemedi (az kayıt)"}:
        return "Geri test tarihleri istatistiksel karşılaştırma için az; karşılaştırma değerlendirilemedi."
    if "geride" in results:
        return ("Tahmin bu işletmenin geçmişinde en az bir ufukta basit bir yöntemden istatistiksel olarak anlamlı "
                "biçimde geride (Diebold-Mariano, %5); kasa tahminine temkinli yaklaşılmalı.")
    if "üstün" in results:
        return ("Tahmin bu işletmenin geçmişinde en iyi basit yöntemden istatistiksel olarak anlamlı biçimde daha "
                "isabetli (Diebold-Mariano, %5).")
    return ("Tahmin ile en iyi basit yöntem arasında istatistiksel olarak anlamlı bir fark yok (Diebold-Mariano, %5); "
            "sapma yüzdeleri aşağıda.")


def render(r: dict) -> str:
    res, sim, gap = r["res"], r["res"]["sim"], r["gap"]
    quality = pd.DataFrame(list(r["quality"].items()), columns=["Ölçüt", "Değer"])
    rec = r["record"]
    record = pd.DataFrame({"Ufuk": [f"{h} gün ({pd.Timestamp(u):%d.%m.%Y} dahil)" for h, u in zip(rec["horizon"], rec["until"])],
                           "Model, kötümser": rec["p10"].map(_tl), "Model, orta (P50)": rec["p50"].map(_tl),
                           "Model, iyimser": rec["p90"].map(_tl), "Vadesinde öder": rec["naive_due"].map(_tl),
                           "Müşteri medyanı": rec["naive_median"].map(_tl),
                           "Son dönemin tahsilat oranı": rec["naive_rate"].map(lambda v: _tl(v) if v == v and v is not None else "–")})
    # Makinece okunur kopya: ufuk dolunca değerlendirme betiği sayıları buradan alır.
    cash_rec = r.get("cash_record", pd.DataFrame())
    cash_table = pd.DataFrame({
        "Ufuk": [f"{h} gün ({pd.Timestamp(u):%d.%m.%Y})" for h, u in zip(cash_rec.get("horizon", []), cash_rec.get("until", []))],
        "Kötümser": cash_rec.get("p10", pd.Series(dtype=float)).map(_tl),
        "Orta (P50)": cash_rec.get("p50", pd.Series(dtype=float)).map(_tl),
        "İyimser": cash_rec.get("p90", pd.Series(dtype=float)).map(_tl),
        "Kasa değişmez": cash_rec.get("naive_flat", pd.Series(dtype=float)).map(_tl)})
    all_rows = pd.concat([rec, cash_rec], ignore_index=True)
    machine = json.dumps({"label": r["label"], "as_of": f"{r['as_of']:%Y-%m-%d}", "opening": float(res["opening"]),
                          "meta": {"surum": VERSION},
                          "record": all_rows.astype(object).where(all_rows.notna(), None).to_dict(orient="records")},
                         ensure_ascii=False, default=float).replace("</", r"<\/")
    weeks = r["weeks"].copy()
    for c in weeks.columns:
        if "(TL)" in c:
            weeks[c] = weeks[c].map(_tl)
    weeks["Eksiye düşme olasılığı"] = weeks["Eksiye düşme olasılığı"].map(_pct)
    accuracy = ""
    if not r["delays"].empty:
        d = r["delays"]
        accuracy += _table(pd.DataFrame({
            "Yöntem": ["Model", "Müşteri her zamanki kadar geç öder", "Son 4 faturanın ortalaması", "Vadesinde öder"],
            "Fatura gecikmesi, ort. hata (gün)": [f"{d[c].mean():.1f}" for c in ("mae_model", "mae_medyan", "mae_son4", "mae_vade")]}))
    if not r["cash"].empty:
        c = r["cash"]
        if r.get("retro"):
            accuracy += (f"<p class=\"note\">Aşama 0, geriye dönük pilot testi: {int(c['tahmin_tarihi_sayisi'].max())} "
                         "haftalık tahmin günü, her biri yalnızca o güne kadarki veriyle (pilot protokolü 1.6). "
                         "İleriye dönük pilotun B1/B2 kararının yerine geçmez.</p>")
        accuracy += _table(pd.DataFrame({
            "Ufuk": [f"{h} gün" for h in c["ufuk_gun"]],
            "Model sapması": [f"%{v:.1f}" for v in c["sapma_model_%"]],
            "Müşteri medyanı sapması": [f"%{v:.1f}" for v in c["sapma_medyan_%"]],
            "Vadesinde öder sapması": [f"%{v:.1f}" for v in c["sapma_vade_%"]],
            "Tahsilat oranı sapması": [f"%{v:.1f}" for v in c["sapma_oran_%"]],
            "İsabet testi (Diebold-Mariano)": list(c.get("dm_sonuc", pd.Series(["–"] * len(c)))),
            "Basel (kötümser uç)": list(c.get("basel_alt", pd.Series(["–"] * len(c)))),
            "Kupiec p": [f"{v:.2f}" if v == v else "–" for v in c.get("kupiec_p", pd.Series([float("nan")] * len(c)))],
            "Tahmin günü": [str(int(v)) for v in c["tahmin_tarihi_sayisi"]],
            "Bant içinde kalan tarih": [_pct(v) for v in c["bant_ici"]]}))
    risk_line = (f"Kötümser senaryoda kasa {sim.breach_day}. günde ({sim.dates[sim.breach_day]:%d.%m.%Y}) eksiye düşüyor; "
                 f"en derin açık {_tl(gap['gap'])}." if sim.breach_day is not None
                 else "Kötümser senaryoda bile kasa 90 gün boyunca artıda kalıyor.")
    if gap.get("k"):
        risk_line += f" Öncelik listesinin ilk {gap['k']} faturası ({_tl(gap['amount'])}) bir hafta içinde tahsil edilirse açık kapanıyor."
    return f"""<!doctype html><html lang="tr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Pilot raporu – {html.escape(r['label'])}</title>
<style>
:root{{--ink:#1d2433;--muted:#5b6475;--line:#d8dce3;--accent:#1f6fb4;--band:rgba(31,111,180,.18);--bad:#b42318;--bg:#fff}}
body{{font:14px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif;color:var(--ink);background:var(--bg);max-width:900px;margin:24px auto;padding:0 16px}}
h1{{font-size:22px;margin:0}} h2{{font-size:16px;margin:28px 0 8px;border-bottom:1px solid var(--line);padding-bottom:4px}}
.muted{{color:var(--muted)}} table{{border-collapse:collapse;width:100%;margin:8px 0}} th,td{{border-bottom:1px solid var(--line);padding:5px 8px;text-align:left}}
th{{color:var(--muted);font-weight:600}} .kpi{{display:flex;gap:24px;flex-wrap:wrap}} .kpi div{{min-width:150px}} .kpi b{{display:block;font-size:20px}}
svg{{width:100%;height:auto}} .band{{fill:var(--band)}} .mid{{fill:none;stroke:var(--accent);stroke-width:2}} .zero{{stroke:var(--bad);stroke-dasharray:4 4}}
.t{{font-size:10px;fill:var(--muted)}} .note{{font-size:12px;color:var(--muted)}} @media print{{body{{margin:0}}}}
</style></head><body>
<h1>KOBİ Nakit Akışı Radarı – pilot raporu</h1>
<p class="muted">{html.escape(r['label'])} · tahmin tarihi {r['as_of']:%d.%m.%Y}</p>
<h2>Özet</h2>
<div class="kpi"><div>Kasa ve banka<b>{_tl(res['opening'])}</b></div><div>Açık alacak<b>{_tl(res['metrics']['open_ar'])}</b></div>
<div>Vadesi geçmiş<b>{_tl(res['metrics']['overdue_ar'])}</b></div><div>90 günde eksiye düşme riski<b>{_pct(sim.prob_any_breach)}</b></div></div>
<p>{html.escape(risk_line)}</p>
<h2>90 günlük kasa</h2>{_band_svg(sim)}
<p class="note">Mavi bant: kasanın %80 olasılıkla içinde kalacağı aralık. Çizgi: orta tahmin (P50, medyan); gerçekleşenin altında ya da üstünde kalma olasılığı eşittir. Kırmızı kesikli: sıfır.</p>
<h2>13 haftalık plan</h2>{_table(weeks)}
<h2>Öncelikli tahsilat (ilk 10)</h2>{_table(r['top'])}
<h2>Tahmin bu işletmenin geçmişinde ne kadar tuttu?</h2>
<p><b>{html.escape(verdict(r['delays'], r['cash']))}</b></p>{accuracy}
<p class="note">Geçmiş tarihlere dönülüp o gün bilinen veriyle tahmin yapıldı ve sonradan gerçekleşenle karşılaştırıldı.
Kasa sapması: o gün açık faturalardan sonraki 14/30 günde tahsil edilen tutardaki hata. Bant içi hedefi %80.</p>
<h2>İleriye dönük kayıt</h2>
<p class="note">Bugün açık faturalardan önümüzdeki günlerde tahsil edilecek tutar (yeni satışlar hariç). Bu sayfa değiştirilmeden
saklanır; ufuk dolduğunda gerçekleşen tahsilatla karşılaştırılır (kısmi ödemeler kendi tarih ve tutarıyla). Pilotun
asıl ölçümü budur (protokol B1).</p>{_table(record)}
<p class="note">Kapanış kasası: bugünkü kasa ve bankadan başlayıp bilinen giderler, borçlar, çekler ve açık faturalarla
7, 14 ve 28 gün sonraki kasa. Gerçekleşen, o gün panele girilen kasa ve banka toplamıdır.</p>{_table(cash_table)}
<script type="application/json" id="ileriye-donuk-kayit">{machine}</script>
<h2>Veri</h2>{_table(quality)}
<h2>Yöntem ve sınırlar</h2>
<p class="note">Gecikme tahmini müşterilerin geçmiş ödeme davranışından öğrenilir (LightGBM kantil regresyonu ile müşteri medyanının birleşimi; az veride yalnızca müşteri medyanı).
Kasa, 2.000 senaryolu Monte Carlo simülasyonuyla hesaplanır; müşterilerin birlikte gecikme eğilimi ve tahmin aralığı, geçmiş tahminlerin
hatasından ölçülür. İki herkese açık gerçek veri setinde model, "müşteri her zamanki kadar geç öder" yöntemiyle başa baş, "vadesinde ödenir"
varsayımından daha isabetli çıkmıştır; "son dönemin tahsilat oranı" yöntemi ise bir veri setinde modelden isabetli, diğerinde
geride kalmıştır (proje belgeleri: DOGRULAMA.md). Bu yüzden rapor, modeli her işletmenin kendi geçmişinde bu yöntemlerle yarıştırır. Gecikmeler hızla kötüleşiyorsa tahmin iyimser kalabilir.
Kur değişimi, yeni kredi ve plan dışı büyük giderler dahil değildir.</p>
</body></html>"""


ONLINE_ETA = 0.1          # adım büyüklüğü (protokol 1.4'te ön kayıtlı)
# Katsayılar için yalnızca sıfır sınırı vardır (bant ters dönmez); yayımlanmış yöntem (Gibbs ve Candès 2021) budur.
# Önceki sürümdeki sınırlar (kötümser >= 1, iyimser >= 0,5) bir kurum ya da yayına dayanmıyordu; sıralı
# laboratuvarda kötümser ucu gereğinden geniş tuttu (1.000 kayıtta aşım %6,3; sınırsız %9,7, Kupiec p = 0,75).
ONLINE_RISK_FLOOR = 0.0
ONLINE_UPPER_FLOOR = 0.0


def track_quantiles(recs: pd.DataFrame, data_end, tail: float = 0.10, eta: float | None = None,
                    lo_floor: float | None = None, hi_floor: float | None = None, lo_floor_late: float | None = None,
                    narrow_after: int = 26) -> tuple[dict, pd.DataFrame]:
    """Uyarlanabilir konformal çıkarım (Gibbs ve Candès 2021; Angelopoulos, Candès ve Tibshirani 2023, P terimi).

    recs sütunları: as_of, until, p10, p50, p90, actual. Kayıtlar tahmin günü sırasıyla işlenir. Her kayda, o gün
    geçerli olan katsayılarla ayarlanmış bant uygulanır: alt = p50 − w_lo (p50 − p10), üst = p50 + w_hi (p90 − p50).
    Katsayılar yalnızca o güne kadar ufku dolmuş kayıtlarla güncellenir: w ← w + eta (aşım − 0,10). Aşım, gerçekleşenin
    o gün GÖSTERİLEN (ayarlanmış) bandın dışında kalmasıdır; geri besleme bu sayede kapanır ve uzun dönemde her uçta
    aşım oranı %10'a yaklaşır. lo_floor_late: `narrow_after` kayıt dolduktan sonra kötümser katsayının alt sınırı
    (verilmezse lo_floor kalır). Dönen: son katsayılar ve kayıt başına ayarlanmış bant."""
    eta = ONLINE_ETA if eta is None else eta
    lo_floor = ONLINE_RISK_FLOOR if lo_floor is None else lo_floor
    hi_floor = ONLINE_UPPER_FLOOR if hi_floor is None else hi_floor
    recs = recs.assign(as_of=pd.to_datetime(recs["as_of"]), until=pd.to_datetime(recs["until"])).sort_values("as_of")
    data_end = pd.Timestamp(data_end)
    w_lo = w_hi = 1.0
    n = 0
    pending: list[dict] = []
    out = []

    def mature(upto):
        nonlocal w_lo, w_hi, n
        ready = sorted((q for q in pending if q["until"] <= upto and q["until"] <= data_end), key=lambda q: q["until"])
        for q in ready:
            floor = lo_floor_late if lo_floor_late is not None and n >= narrow_after else lo_floor
            w_lo = max(floor, w_lo + eta * (float(q["actual"] < q["lo"]) - tail))
            w_hi = max(hi_floor, w_hi + eta * (float(q["actual"] > q["hi"]) - tail))
            n += 1
            pending.remove(q)

    for r in recs.itertuples():
        mature(r.as_of)
        q = {"as_of": r.as_of, "until": r.until, "actual": r.actual,
             "lo": r.p50 - w_lo * (r.p50 - r.p10), "hi": r.p50 + w_hi * (r.p90 - r.p50), "w_lo": w_lo, "w_hi": w_hi}
        pending.append(q)
        out.append(q)
    mature(data_end)
    return {"lo": w_lo, "hi": w_hi, "n": n}, pd.DataFrame(out)


def online_adjustment(table: pd.DataFrame, later: pd.DataFrame, events: pd.DataFrame | None = None,
                      tail: float = 0.10) -> dict:
    """Pilot tahsilat kayıtlarıyla çevrimiçi kantil izleme (track_quantiles). Kayıt yoksa (1, 1). Adım küçük olduğu
    için (0,1 × 0,1 = haftada en fazla %1 daralma) az kayıtla bant ancak çok az daralabilir.

    Düzeltme (18.10.2026): önceki sürüm gerçekleşeni ayarlanmamış banda göre değerlendiriyordu; bu durumda katsayı
    dengeye gelmez (ham bant az aşılıyorsa alt sınıra yapışır, çok aşılıyorsa sınırsız büyür)."""
    if table is None or not len(table):
        return {"lo": 1.0, "hi": 1.0, "n": 0}
    rec = table[table.get("target", pd.Series("tahsilat", index=table.index)).fillna("tahsilat") == "tahsilat"]
    if not len(rec):
        return {"lo": 1.0, "hi": 1.0, "n": 0}
    events = collection_events(later) if events is None else events
    issued = later.set_index(later["invoice_id"].astype(str))["issue_date"]
    ev = events.assign(issue=events["invoice_id"].astype(str).map(issued))
    data_end = max(later["issue_date"].max(), events["date"].max() if len(events) else later["issue_date"].max())
    rec = rec.assign(until=pd.to_datetime(rec["until"]), as_of=pd.to_datetime(rec["as_of"]))
    rec = rec.assign(actual=[float(ev.loc[(ev["issue"] <= a) & (ev["date"] > a) & (ev["date"] <= u), "amount"].sum())
                             for a, u in zip(rec["as_of"], rec["until"])])
    if "p50" not in rec:
        rec = rec.assign(p50=(rec["p10"] + rec["p90"]) / 2)
    state, _ = track_quantiles(rec[["as_of", "until", "p10", "p50", "p90", "actual"]], data_end, tail)
    return state


def records_from_table(table: pd.DataFrame) -> list[dict]:
    """Panelin sakladığı kayıt tablosunu score() girdisine çevirir: tarih başına bir kayıt."""
    out = []
    for as_of, g in table.groupby("as_of"):
        meta = g["meta"].dropna().iloc[0] if "meta" in g and g["meta"].notna().any() else "{}"
        opening = g["opening"].dropna().iloc[0] if "opening" in g and g["opening"].notna().any() else None
        rows = g.drop(columns=["as_of", "created", "meta", "opening"], errors="ignore")
        out.append({"as_of": as_of, "opening": opening, "meta": json.loads(meta),
                    "record": rows.astype(object).where(rows.notna(), None).to_dict(orient="records")})
    return out


def record_due(table: pd.DataFrame, as_of, last_activity, today=None) -> str | None:
    """Bugün yeni kayıt alınmalı mı? Alınmamalıysa nedeni döner (None = alınmalı).

    Kayıt yalnızca bugünün tahmininden alınır (geçmiş tarihli tahmin geri testtir, ileriye dönük değil),
    veri bir haftadan eskiyse alınmaz (bu arada gelen ödemeler açık görünür) ve haftada bir alınır."""
    as_of, today = pd.Timestamp(as_of).normalize(), pd.Timestamp(today or pd.Timestamp.now()).normalize()
    if as_of != today:
        return "Tahmin tarihi bugün değil; ileriye dönük kayıt yalnızca bugünün tahmininden alınır."
    if last_activity is None or (as_of - pd.Timestamp(last_activity)).days > 7:
        return "Verideki son hareket bir haftadan eski; güncel dosyaları yükleyince kayıt alınır."
    if len(table) and (as_of - pd.to_datetime(table["as_of"]).max()).days < 7:
        return "Bu haftanın kaydı alındı."
    return None


def read_record(page: str) -> dict:
    """Kaydedilmiş bir pilot raporundan ileriye dönük kaydı okur."""
    start = page.index('id="ileriye-donuk-kayit">') + len('id="ileriye-donuk-kayit">')
    return json.loads(page[start:page.index("</script>", start)])


def score(records: list[dict], later: pd.DataFrame, events: pd.DataFrame | None = None,
          n_boot: int = 1000, seed: int = 0, margins: dict | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Ufku dolmuş kayıtları sonradan gelen veriyle karşılaştırır. Dönen ikinci tablo protokol ölçütleridir.

    Hedef A (tahsilat): gerçekleşen, tahmin günü açık olan faturalara ufuk içinde gelen tahsilat olaylarının
    toplamıdır; kısmi ödemeler kendi tarih ve tutarıyla sayılır (`events`, yoksa faturalardan türetilir).
    Hedef B (kapanış kasası): gerçekleşen, ufkun sonuna en yakın (±3 gün) kayıtta girilmiş güncel kasa.
    Haftalık kayıtların ufukları üst üste biner; bu yüzden kayıtlar bağımsız sayılmaz: model ile en iyi
    basit yöntem arasındaki farkın güven aralığı, tarih bloklarıyla yeniden örneklenerek (blok bootstrap)
    hesaplanır. Banka eşleşmesi düşük olan kayıtlar uyarılıdır ve B1'e girmez.

    margins: {ufuk: M2} (protokol 1.7; ilk Aşama 0 testinde dondurulur). B1 tahsilatta marjlı eşdeğerlik
    kararıdır (b1_decision); Diebold-Mariano sonucu ayrıca betimleyici olarak verilir."""
    events = collection_events(later) if events is None else events
    issued = later.set_index(later["invoice_id"].astype(str))["issue_date"]
    ev = events.assign(issue=events["invoice_id"].astype(str).map(issued))
    data_end = max(later["issue_date"].max(), events["date"].max() if len(events) else later["issue_date"].max())
    openings = {pd.Timestamp(r["as_of"]): r.get("opening") for r in records
                if r.get("opening") is not None and r.get("meta", {}).get("acilis_guncel", False)}
    rows = []
    for rec in records:
        as_of = pd.Timestamp(rec["as_of"])
        match = rec.get("meta", {}).get("eslesme_orani")
        flagged = match is not None and match < MIN_MATCH_RATE
        for r in rec["record"]:
            until, target = pd.Timestamp(r["until"]), r.get("target") or "tahsilat"
            if target == "kasa":
                near = [d for d in openings if abs((d - until).days) <= 3]
                if not near:
                    continue
                actual = float(openings[min(near, key=lambda d: abs((d - until).days))])
                base = {"sabit": r.get("naive_flat")}
            else:
                if until > data_end:
                    continue                                              # ufuk henüz dolmadı
                hit = (ev["issue"] <= as_of) & (ev["date"] > as_of) & (ev["date"] <= until)
                actual = float(ev.loc[hit, "amount"].sum())
                base = {"vade": r.get("naive_due"), "medyan": r.get("naive_median"), "oran": r.get("naive_rate")}
            rows.append({"hedef": target, "tahmin_tarihi": as_of.date(), "ufuk_gun": int(r["horizon"]),
                         "gerceklesen": actual, "p10": r["p10"], "model": r["p50"], "p90": r["p90"],
                         **{k: float("nan") if v is None else float(v) for k, v in base.items()},
                         "bant_ici": r["p10"] <= actual <= r["p90"], "uyari": flagged})
    detail = pd.DataFrame(rows)
    if detail.empty:
        return detail, pd.DataFrame()
    # Eksik haftalar ve güncellenmemiş kasa (1.6, betimleyici): sonuçların kaç kayda dayandığı açıkça görünsün.
    days = sorted({pd.Timestamp(r["as_of"]).normalize() for r in records})
    weeks = (days[-1] - days[0]).days // 7 + 1 if days else 0
    missing_weeks = max(0, weeks - len({(d - days[0]).days // 7 for d in days}))
    stale_cash = sum(1 for r in records if not r.get("meta", {}).get("acilis_guncel", False))
    summary = []
    for (target, h), g_all in detail.groupby(["hedef", "ufuk_gun"]):
        g = g_all[~g_all["uyari"]] if target == "tahsilat" else g_all
        if g.empty:
            continue
        methods = ["vade", "medyan", "oran"] if target == "tahsilat" else ["sabit"]
        err = lambda d, m: (d[m] - d["gerceklesen"]).abs().sum(min_count=len(d)) / (d["gerceklesen"].abs().sum() or float("nan")) * 100
        e = {m: err(g, m) for m in ["model"] + methods}
        row = {"hedef": target, "ufuk_gun": h, "kayit": len(g), "uyarili_kayit": int(g_all["uyari"].sum()),
               "eksik_hafta": missing_weeks, "kasa_guncel_olmayan_kayit": stale_cash,
               "sapma_model_%": e["model"], **{f"sapma_{m}_%": e[m] for m in methods},
               "bant_ici": g["bant_ici"].mean(),
               "bant_genisligi_%": (g["p90"] - g["p10"]).sum() / (g["gerceklesen"].abs().sum() or float("nan")) * 100,
               "aralik_skoru_%": _interval_score(g["p10"], g["p90"], g["gerceklesen"]).sum()
               / (g["gerceklesen"].abs().sum() or float("nan")) * 100}
        # Blok bootstrap: ufkun kapsadığı hafta sayısı kadar ardışık kayıt birlikte örneklenir.
        strong = [m for m in methods if m != "vade" and g[m].notna().all()]
        dates = sorted(g["tahmin_tarihi"].unique())
        block = max(1, int(np.ceil(h / 7)))
        ci95 = None
        if strong and len(dates) >= 4:
            diffs = block_bootstrap(g, "tahmin_tarihi", block,
                                    lambda d: err(d, "model") - min(err(d, m) for m in strong), n_boot, seed)
            row["fark_guven_araligi"] = ci(diffs, 90)
            ci95 = ci(diffs)
            row["fark_tahmin"] = float(err(g, "model") - min(err(g, m) for m in strong))
            # En az iki bağımsız blok yoksa bootstrap değişkenliği ölçemez (bütün örnekler aynı olur); standart hata
            # verilmez ve işletme birleşik analizde "yetersiz kayıt" olarak raporlanır.
            row["fark_se"] = float(np.std(diffs, ddof=1)) if len(dates) >= 2 * block else float("nan")
        else:
            row["fark_guven_araligi"] = None
        row["fark_guven_araligi_95"] = ci95
        overlap = max(1, int(np.ceil(h / 7)))                    # haftalık kayıtlar: ufuk kaç hafta üst üste biner
        band = interval_report(g["gerceklesen"], g["p10"], g["p90"])
        row.update({"alt_asim": band["below"], "ust_asim": band["above"], "basel_alt": band["basel_lower"]["zone"],
                    "kupiec_p": band["kupiec_central"]["p_value"], "B2": interval_passes(band)})
        # Basel ve Kupiec aşımların bağımsız olduğunu varsayar (Christoffersen 1998); üst üste binen ufuklarda bu
        # tutmaz. Betimleyici kontrol: her `block` haftada bir kayıt (örtüşmeyen alt örneklem).
        sub = g[g["tahmin_tarihi"].isin(dates[::block])]
        sub_band = interval_report(sub["gerceklesen"], sub["p10"], sub["p90"])
        row.update({"ortusmeyen_kayit": len(sub), "ortusmeyen_alt_asim": sub_band["below"],
                    "ortusmeyen_ust_asim": sub_band["above"], "ortusmeyen_kupiec_p": sub_band["kupiec_central"]["p_value"]})
        errors = pd.DataFrame({m: (g[m] - g["gerceklesen"]).abs() for m in ["model"] + methods})
        if target == "tahsilat":
            acc = accuracy_test(errors, overlap)
            m2 = (margins or {}).get(int(h))
            vs_due = diebold_mariano(errors["model"], errors["vade"], overlap) if g["vade"].notna().all() else {}
            passed, result = b1_decision(ci95, m2, vs_due.get("p_worse", 1.0) < SIGNIFICANCE)
            row.update({"B1_marj": m2, "B1_sonuc": result})
            acc = {**acc, "B1": passed}
        else:                                                    # kapanış kasası: tek karşılaştırma "kasa değişmez"
            dm = diebold_mariano(errors["model"], errors["sabit"], overlap)
            res = (None if not np.isfinite(dm["p_worse"]) else
                   "geride" if dm["p_worse"] < SIGNIFICANCE else ("üstün" if dm["p_better"] < SIGNIFICANCE else "eşdeğer"))
            acc = {"B1": None if res is None else res != "geride", "sonuc": res or "değerlendirilemedi (az kayıt)"}
        row.update({"B1": acc["B1"], "dm_sonuc": acc["sonuc"]})
        summary.append(row)
    return detail, pd.DataFrame(summary)


if __name__ == "__main__":
    import sys
    from pathlib import Path

    from .ingest import load_invoices

    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) not in (3, 4):
        sys.exit("Kullanım: python -m radar.pilot <raporlar_klasoru> <guncel_faturalar.csv> [guncel_ekstre.csv]")
    pages = [p.read_text(encoding="utf-8") for p in sorted(Path(sys.argv[1]).glob("*.html"))]
    later, _ = load_invoices(sys.argv[2])
    events = None
    if len(sys.argv) == 4:                     # banka ekstresi varsa kısmi ödemeler kendi tarihleriyle sayılır
        from .ingest import load_payments
        from .reconcile import reconcile
        paid, allocations, _ = reconcile(later.assign(open_amount=later["amount"], paid_date=pd.NaT),
                                         load_payments(sys.argv[3])[0])
        events = collection_events(paid, allocations)
    detail, summary = score([read_record(p) for p in pages], later, events=events)
    pd.set_option("display.width", 200)
    print(detail.to_string(index=False) if len(detail) else "Ufku dolmuş kayıt yok.")
    print(summary.round(2).to_string(index=False) if len(summary) else "")
