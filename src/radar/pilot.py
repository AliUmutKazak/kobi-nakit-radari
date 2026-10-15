"""Pilot raporu: bir işletme için tek sayfalık, yazdırılabilir HTML.

İçerik ve ölçütler docs/pilot/PILOT_PROTOKOLU.md'de önceden tanımlanmıştır; rapor yalnızca onları
hesaplar. Hiçbir dış kaynağa bağlanmaz (grafik, sayfanın içine çizilen SVG'dir).
"""
from __future__ import annotations

import html
import json

import pandas as pd

from . import actions
from .anonymize import invoice_aliases, pseudonym
from .open_data import delay_study
from .synthetic import observe
from .pipeline import forecast, gap_summary, naive_collections, weekly_table


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
    """Kasa bandı (P10–P90) ve beklenen çizgi; sıfır çizgisi kesikli."""
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
        res = forecast(obs, as_of, opening, flows, cheques=cheques)
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
    delays = delay_study(obs, origins=4, step=60) if history_days >= 300 else pd.DataFrame()
    # Veri tahmin tarihinden eskiyse, son hareketten sonraki ödemeler bilinmez; geri test orada biter.
    cash = cash_backtest(obs, min(as_of, last)) if history_days >= 300 else pd.DataFrame()
    return {"label": label, "as_of": as_of, "res": res, "quality": quality, "delays": delays, "cash": cash,
            "gap": gap_summary(res), "weeks": weekly_table(res), "top": _top(res, key, obs),
            "record": forward_record(obs, as_of)}


def cash_backtest(obs: pd.DataFrame, as_of, horizons=(14, 30), origins: int = 4, step: int = 21,
                  n_sims: int = 500) -> pd.DataFrame:
    """Kasa düzeyinde geri test: geçmiş tarihlerde, o gün açık faturalardan 14 ve 30 günde tahsil edilen tutar.

    open_data.cash_study ile aynı ölçüt; farkı, her tahmin tarihinde tek simülasyondan iki ufkun birden
    okunmasıdır (açılış sıfır, gider ve yeni satış yokken kasa yolu birikmiş tahsilattır). Panelde rapor
    süresini yarıdan fazla kısaltır. Her ufuk veri kesiminden (as_of) önce biter."""
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
    bt = pd.DataFrame(rows)
    out = []
    for h, g in bt.groupby("h"):
        total = g["actual"].sum() or float("nan")
        err = lambda col: (g[col] - g["actual"]).abs().sum() / total * 100
        out.append({"ufuk_gun": h, "tahmin_tarihi_sayisi": len(g), "sapma_model_%": err("p50"),
                    "sapma_medyan_%": err("naive_median"), "sapma_vade_%": err("naive_due"),
                    "sapma_oran_%": err("naive_rate"),
                    "bant_ici": ((g["p10"] <= g["actual"]) & (g["actual"] <= g["p90"])).mean()})
    return pd.DataFrame(out)


def forward_record(obs: pd.DataFrame, as_of, horizons=(14, 30), n_sims: int = 1000) -> pd.DataFrame:
    """İleriye dönük kayıt: bugün açık faturalardan önümüzdeki 14 ve 30 günde tahsil edilecek tutar;
    model ve iki basit yöntem. Pilotun asıl ölçümü budur (protokol B1): rapor her hafta değiştirilmeden
    saklanır, ufuk dolunca gerçekleşenle karşılaştırılır. Geri testten farkı, sonucun tahmin anında
    hiç kimse tarafından bilinmemesidir."""
    as_of = pd.Timestamp(as_of)
    book = obs[(obs["issue_date"] <= as_of) & ~(obs["paid_date"] <= as_of) & (obs["open_amount"] > 0)]
    book = book.assign(amount=book["open_amount"])
    # Tek simülasyon yeter: açılış kasası sıfır, gider ve yeni satış yokken kasa yolu, o güne kadarki
    # tahsilatın kendisidir; h. günün yüzdelikleri h günlük tahsilatın yüzdelikleridir.
    sim = forecast(obs, as_of, 0.0, pd.DataFrame({"date": [], "amount": []}), horizon=max(horizons), n_sims=n_sims,
                   include_projected=False)["sim"]
    rows = []
    for h in horizons:
        end = as_of + pd.Timedelta(days=h)
        lo, mid, hi = sim.p10[h], sim.p50[h], sim.p90[h]
        rows.append({"horizon": h, "until": f"{end:%Y-%m-%d}", "p10": round(lo), "p50": round(mid), "p90": round(hi),
                     **{k: round(v) if v == v else None for k, v in naive_collections(obs, book, as_of, end).items()}})
    return pd.DataFrame(rows)


def _top(res: dict, key: str | None, obs: pd.DataFrame) -> pd.DataFrame:
    top = res["ranked"][res["ranked"]["actionable"]].head(10)
    names = top["customer_id"].map(lambda c: pseudonym(key, c)[0]) if key else top["customer_name"]
    # Takma numara, anonim paketteki numarayla aynı olsun diye fatura yılı faturanın kendi tarihinden alınır.
    numbers = top["invoice_id"].astype(str).map(invoice_aliases(obs[obs["invoice_id"].isin(top["invoice_id"])], key))         if key else top["invoice_id"]
    top = pd.DataFrame({"Fatura": numbers, "Müşteri": names,
                        "Vade": top["due_date"].dt.strftime("%d.%m.%Y"), "Tutar": top["open_amount"].map(_tl),
                        "Gecikme (gün)": top["days_overdue"], "Risk": top["p_late"].map(_pct)})
    return top


# Önceden kayıtlı eşik (PILOT_PROTOKOLU.md, ölçüt B1): model, kasa düzeyinde müşteri medyanından en fazla
# bu kadar puan kötüyse "başa baş" sayılır. Pilot verisi görülmeden belirlendi; sonradan değiştirilmez.
NONINFERIORITY_POINTS = 2.0


def passes_b1(model: float, due: float, median: float, rate: float) -> bool:
    """Ölçüt B1: model, "vadesinde öder"den iyi ve iki güçlü basit yöntemin iyisinden en fazla eşik kadar kötü."""
    best = min(v for v in (median, rate) if v == v)
    return model < due and model <= best + NONINFERIORITY_POINTS


def verdict(delays: pd.DataFrame, cash: pd.DataFrame) -> str:
    """Protokoldeki karar kuralı (ölçüt B1), kasa düzeyindeki ortalama sapmaya göre."""
    if cash is None or cash.empty:
        return "Geri test için yeterli geçmiş yok (en az 10 aylık fatura gerekir); isabet ölçülemedi."
    model, median, due = (cash[c].mean() for c in ("sapma_model_%", "sapma_medyan_%", "sapma_vade_%"))
    rate = cash["sapma_oran_%"].mean() if "sapma_oran_%" in cash else float("nan")
    best = min(v for v in (median, rate) if v == v)
    if model <= best and model < due:
        return "Tahmin, bu işletmenin geçmişinde bütün basit yöntemlerden daha isabetli."
    if passes_b1(model, due, median, rate):
        return "Tahmin, 'vadesinde ödenir' varsayımından daha isabetli; en iyi basit yöntemle başa baş."
    if model < due:
        return ("Tahmin, 'vadesinde ödenir' varsayımından daha isabetli, ancak en iyi basit yöntemin gerisinde; "
                "bu işletmede kasa tahminine temkinli yaklaşılmalı.")
    return "Tahmin bu işletmede basit yöntemlerden daha isabetli değil; sonuçlara temkinli yaklaşılmalı."


def render(r: dict) -> str:
    res, sim, gap = r["res"], r["res"]["sim"], r["gap"]
    quality = pd.DataFrame(list(r["quality"].items()), columns=["Ölçüt", "Değer"])
    rec = r["record"]
    record = pd.DataFrame({"Ufuk": [f"{h} gün ({pd.Timestamp(u):%d.%m.%Y} dahil)" for h, u in zip(rec["horizon"], rec["until"])],
                           "Model, kötümser": rec["p10"].map(_tl), "Model, beklenen": rec["p50"].map(_tl),
                           "Model, iyimser": rec["p90"].map(_tl), "Vadesinde öder": rec["naive_due"].map(_tl),
                           "Müşteri medyanı": rec["naive_median"].map(_tl),
                           "Son dönemin tahsilat oranı": rec["naive_rate"].map(lambda v: _tl(v) if v == v and v is not None else "–")})
    # Makinece okunur kopya: ufuk dolunca değerlendirme betiği sayıları buradan alır.
    machine = json.dumps({"label": r["label"], "as_of": f"{r['as_of']:%Y-%m-%d}",
                          "record": rec.to_dict(orient="records")}, ensure_ascii=False).replace("</", r"<\/")
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
<p class="note">Mavi bant: kasanın %80 olasılıkla içinde kalacağı aralık. Çizgi: beklenen. Kırmızı kesikli: sıfır.</p>
<h2>13 haftalık plan</h2>{_table(weeks)}
<h2>Öncelikli tahsilat (ilk 10)</h2>{_table(r['top'])}
<h2>Tahmin bu işletmenin geçmişinde ne kadar tuttu?</h2>
<p><b>{html.escape(verdict(r['delays'], r['cash']))}</b></p>{accuracy}
<p class="note">Geçmiş tarihlere dönülüp o gün bilinen veriyle tahmin yapıldı ve sonradan gerçekleşenle karşılaştırıldı.
Kasa sapması: o gün açık faturalardan sonraki 14/30 günde tahsil edilen tutardaki hata. Bant içi hedefi %80.</p>
<h2>İleriye dönük kayıt</h2>
<p class="note">Bugün açık faturalardan önümüzdeki günlerde tahsil edilecek tutar (yeni satışlar hariç). Bu sayfa değiştirilmeden
saklanır; ufuk dolduğunda gerçekleşen tahsilatla karşılaştırılır. Pilotun asıl ölçümü budur.</p>{_table(record)}
<script type="application/json" id="ileriye-donuk-kayit">{machine}</script>
<h2>Veri</h2>{_table(quality)}
<h2>Yöntem ve sınırlar</h2>
<p class="note">Gecikme tahmini müşterilerin geçmiş ödeme davranışından öğrenilir (LightGBM kantil regresyonu; az veride müşteri medyanı).
Kasa, 2.000 senaryolu Monte Carlo simülasyonuyla hesaplanır; müşterilerin birlikte gecikme eğilimi ve tahmin aralığı, geçmiş tahminlerin
hatasından ölçülür. İki herkese açık gerçek veri setinde model, "müşteri her zamanki kadar geç öder" yöntemiyle başa baş, "vadesinde ödenir"
varsayımından daha isabetli çıkmıştır; "son dönemin tahsilat oranı" yöntemi ise bir veri setinde modelden isabetli, diğerinde
geride kalmıştır (proje belgeleri: DOGRULAMA.md). Bu yüzden rapor, modeli her işletmenin kendi geçmişinde bu yöntemlerle yarıştırır. Gecikmeler hızla kötüleşiyorsa tahmin iyimser kalabilir.
Kur değişimi, yeni kredi ve plan dışı büyük giderler dahil değildir.</p>
</body></html>"""


def records_from_table(table: pd.DataFrame) -> list[dict]:
    """Panelin sakladığı kayıt tablosunu score() girdisine çevirir."""
    return [{"as_of": as_of, "record": g.drop(columns=["as_of", "created"], errors="ignore").to_dict(orient="records")}
            for as_of, g in table.groupby("as_of")]


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


def score(records: list[dict], later: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Ufku dolmuş kayıtları, sonradan gelen veriyle (aynı işletmenin güncel fatura tablosu) karşılaştırır.

    Gerçekleşen: tahmin günü açık olup ufuk içinde ödenen faturaların tutarı. Kısmi ödemeler fatura
    tutarı üzerinden sayılır (yaklaşım). Dönen ikinci tablo protokoldeki B1 ve B2 ölçütleridir."""
    rows = []
    data_end = later[["issue_date", "paid_date"]].max().max()
    for rec in records:
        as_of = pd.Timestamp(rec["as_of"])
        was_open = (later["issue_date"] <= as_of) & ~(later["paid_date"] <= as_of)
        for r in rec["record"]:
            until = pd.Timestamp(r["until"])
            if until > data_end:
                continue                                                  # ufuk henüz dolmadı
            actual = float(later.loc[was_open & (later["paid_date"] <= until), "amount"].sum())
            rows.append({"tahmin_tarihi": as_of.date(), "ufuk_gun": r["horizon"], "gerceklesen": actual,
                         "model": r["p50"], "vade": r["naive_due"], "medyan": r["naive_median"],
                         "oran": r["naive_rate"] if r.get("naive_rate") is not None else float("nan"),
                         "bant_ici": r["p10"] <= actual <= r["p90"]})
    detail = pd.DataFrame(rows)
    if detail.empty:
        return detail, pd.DataFrame()
    summary = []
    for h, g in detail.groupby("ufuk_gun"):
        total = g["gerceklesen"].sum() or float("nan")
        err = {m: (g[m] - g["gerceklesen"]).abs().sum(min_count=len(g)) / total * 100
               for m in ("model", "vade", "medyan", "oran")}
        summary.append({"ufuk_gun": h, "kayit": len(g), "sapma_model_%": err["model"], "sapma_medyan_%": err["medyan"],
                        "sapma_oran_%": err["oran"], "sapma_vade_%": err["vade"], "bant_ici": g["bant_ici"].mean(),
                        "B1_gecti": passes_b1(err["model"], err["vade"], err["medyan"], err["oran"]),
                        "B2_gecti": g["bant_ici"].mean() >= COVERAGE_FLOOR})
    return detail, pd.DataFrame(summary)


# Önceden kayıtlı (protokol B2): kötümser–iyimser bandın içinde kalan kayıt oranı en az bu kadar olmalı.
# Hedef %80; açık verilerde kasa bandı %62–100 arasında çıktığı için alt sınır %70 alındı.
COVERAGE_FLOOR = 0.70


if __name__ == "__main__":
    import sys
    from pathlib import Path

    from .ingest import load_invoices

    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) != 3:
        sys.exit("Kullanım: python -m radar.pilot <raporlar_klasoru> <guncel_faturalar.csv>")
    pages = [p.read_text(encoding="utf-8") for p in sorted(Path(sys.argv[1]).glob("*.html"))]
    later, _ = load_invoices(sys.argv[2])
    detail, summary = score([read_record(p) for p in pages], later)
    pd.set_option("display.width", 200)
    print(detail.to_string(index=False) if len(detail) else "Ufku dolmuş kayıt yok.")
    print(summary.round(2).to_string(index=False) if len(summary) else "")
