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
from .standards import SIGNIFICANCE, diebold_mariano, interval_report, passes as interval_passes

VERSION = "2026.10.20"            # tahmin kaydına yazılır: hangi kod sürümüyle üretildiği
MIN_HISTORY_DAYS = 365            # protokol 2. bölüm: en az 12 aylık fatura geçmişi; altında geri test yapılmaz
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
          n_payments: int | None = None, res: dict | None = None, key: str | None = None) -> dict:
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
    cash = cash_backtest(obs, min(as_of, last)) if history_days >= MIN_HISTORY_DAYS else pd.DataFrame()
    return {"label": label, "as_of": as_of, "res": res, "quality": quality, "delays": delays, "cash": cash,
            "gap": gap_summary(res), "weeks": weekly_table(res), "top": _top(res, key, obs),
            "record": forward_record(obs, as_of, events=res.get("events") if isinstance(res, dict) else None,
                                     payments_through=res["info"].get("payments_through")), "cash_record": cash_record(res)}


def cash_backtest(obs: pd.DataFrame, as_of, horizons=(14, 30), origins: int = 4, step: int = 21,
                  n_sims: int = 500) -> pd.DataFrame:
    """Kasa düzeyinde geri test: geçmiş tarihlerde, o gün açık faturalardan 14 ve 30 günde tahsil edilen tutar.

    open_data.cash_study ile aynı ölçüt; farkı, her tahmin tarihinde tek simülasyondan iki ufkun birden
    okunmasıdır (açılış sıfır, gider ve yeni satış yokken kasa yolu birikmiş tahsilattır). Her ufuk veri
    kesiminden (as_of) önce biter. Sapmanın yanında bandın ortalama genişliği ve aralık skoru da verilir:
    yalnızca "bant içinde kaldı mı" sorusu, gereksiz geniş bandı ödüllendirir."""
    as_of, H = pd.Timestamp(as_of), max(horizons)
    full = obs.assign(true_paid_date=obs["paid_date"])
    rows = []
    for k in range(origins):
        t = as_of - pd.Timedelta(days=H + k * step)
        past = observe(full, t)
        sim = forecast(past, t, 0.0, pd.DataFrame({"date": [], "amount": []}), H, n_sims,
                       include_projected=False, seed=k)["sim"]
        was_open = (full["issue_date"] <= t) & ~(full["true_paid_date"] <= t)
        for h in horizons:
            end = t + pd.Timedelta(days=h)
            rows.append({"h": h, "actual": full.loc[was_open & (full["true_paid_date"] <= end), "amount"].sum(),
                         "p10": sim.p10[h], "p50": sim.p50[h], "p90": sim.p90[h],
                         **naive_collections(past, full[was_open], t, end)})
    return summarize_backtest(pd.DataFrame(rows), step)


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
                    "B2": interval_passes(band)})
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
        accuracy += _table(pd.DataFrame({
            "Ufuk": [f"{h} gün" for h in c["ufuk_gun"]],
            "Model sapması": [f"%{v:.1f}" for v in c["sapma_model_%"]],
            "Müşteri medyanı sapması": [f"%{v:.1f}" for v in c["sapma_medyan_%"]],
            "Vadesinde öder sapması": [f"%{v:.1f}" for v in c["sapma_vade_%"]],
            "Tahsilat oranı sapması": [f"%{v:.1f}" for v in c["sapma_oran_%"]],
            "İsabet testi (Diebold-Mariano)": list(c.get("dm_sonuc", pd.Series(["–"] * len(c)))),
            "Basel (kötümser uç)": list(c.get("basel_alt", pd.Series(["–"] * len(c)))),
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
          n_boot: int = 1000, seed: int = 0) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Ufku dolmuş kayıtları sonradan gelen veriyle karşılaştırır. Dönen ikinci tablo protokol ölçütleridir.

    Hedef A (tahsilat): gerçekleşen, tahmin günü açık olan faturalara ufuk içinde gelen tahsilat olaylarının
    toplamıdır; kısmi ödemeler kendi tarih ve tutarıyla sayılır (`events`, yoksa faturalardan türetilir).
    Hedef B (kapanış kasası): gerçekleşen, ufkun sonuna en yakın (±3 gün) kayıtta girilmiş güncel kasa.
    Haftalık kayıtların ufukları üst üste biner; bu yüzden kayıtlar bağımsız sayılmaz: model ile en iyi
    basit yöntem arasındaki farkın güven aralığı, tarih bloklarıyla yeniden örneklenerek (blok bootstrap)
    hesaplanır. Banka eşleşmesi düşük olan kayıtlar uyarılıdır ve B1'e girmez."""
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
    rng = np.random.default_rng(seed)
    summary = []
    for (target, h), g_all in detail.groupby(["hedef", "ufuk_gun"]):
        g = g_all[~g_all["uyari"]] if target == "tahsilat" else g_all
        if g.empty:
            continue
        methods = ["vade", "medyan", "oran"] if target == "tahsilat" else ["sabit"]
        err = lambda d, m: (d[m] - d["gerceklesen"]).abs().sum(min_count=len(d)) / (d["gerceklesen"].abs().sum() or float("nan")) * 100
        e = {m: err(g, m) for m in ["model"] + methods}
        row = {"hedef": target, "ufuk_gun": h, "kayit": len(g), "uyarili_kayit": int(g_all["uyari"].sum()),
               "sapma_model_%": e["model"], **{f"sapma_{m}_%": e[m] for m in methods},
               "bant_ici": g["bant_ici"].mean(),
               "bant_genisligi_%": (g["p90"] - g["p10"]).sum() / (g["gerceklesen"].abs().sum() or float("nan")) * 100,
               "aralik_skoru_%": _interval_score(g["p10"], g["p90"], g["gerceklesen"]).sum()
               / (g["gerceklesen"].abs().sum() or float("nan")) * 100}
        # Blok bootstrap: ufkun kapsadığı hafta sayısı kadar ardışık kayıt birlikte örneklenir.
        strong = [m for m in methods if m != "vade" and g[m].notna().all()]
        dates = sorted(g["tahmin_tarihi"].unique())
        block = max(1, int(np.ceil(h / 7)))
        if strong and len(dates) >= 4:
            diffs = []
            for _ in range(n_boot):
                starts = rng.integers(0, len(dates), int(np.ceil(len(dates) / block)))
                pick = [dates[(s + j) % len(dates)] for s in starts for j in range(block)][:len(dates)]
                d = pd.concat([g[g["tahmin_tarihi"] == x] for x in pick])
                diffs.append(err(d, "model") - min(err(d, m) for m in strong))
            row["fark_guven_araligi"] = (float(np.percentile(diffs, 5)), float(np.percentile(diffs, 95)))
        else:
            row["fark_guven_araligi"] = None
        overlap = max(1, int(np.ceil(h / 7)))                    # haftalık kayıtlar: ufuk kaç hafta üst üste biner
        band = interval_report(g["gerceklesen"], g["p10"], g["p90"])
        row.update({"alt_asim": band["below"], "ust_asim": band["above"], "basel_alt": band["basel_lower"]["zone"],
                    "kupiec_p": band["kupiec_central"]["p_value"], "B2": interval_passes(band)})
        errors = pd.DataFrame({m: (g[m] - g["gerceklesen"]).abs() for m in ["model"] + methods})
        if target == "tahsilat":
            acc = accuracy_test(errors, overlap)
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
