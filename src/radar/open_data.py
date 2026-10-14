"""Herkese açık gerçek fatura verileriyle doğrulama.

Sentetik veri modelin kendi varsayımları içinde tutarlı olduğunu gösterir; gerçek dünyada
işe yarayıp yaramadığını göstermez. Bu modül, Małkus, Bobek ve Nalepa'nın (arXiv:2511.03631,
2026) KOBİ çalışmasında da kullanılan iki açık veri setini projenin standart tablosuna çevirir
ve modeli basit yöntemlere karşı geçmiş tarihlerde sınar:

- IBM Late Payment Histories (Kaggle: hhenry/finance-factoring-ibm-late-payment-histories),
  yaklaşık 2.466 fatura.
- Payment Date Dataset (Kaggle: rajattomar132/payment-date-dataset), yaklaşık 50.000 satır.

Veriler Kaggle hesabıyla indirilir; bu modül dosya yolunu alır, internetten bir şey çekmez.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .features import build_features
from .model import QS, fit_model, training_frame
from .pipeline import backtest_own, censor

CANONICAL = ["invoice_id", "customer_id", "customer_name", "vkn", "issue_date", "due_date", "amount", "paid_date",
             "open_amount"]


def _finish(df: pd.DataFrame) -> pd.DataFrame:
    df = df.dropna(subset=["invoice_id", "issue_date", "due_date", "amount"])
    df = df[df["amount"] > 0].drop_duplicates("invoice_id")
    df["vkn"] = ""
    df["open_amount"] = np.where(df["paid_date"].isna(), df["amount"], 0.0)
    return df[CANONICAL].sort_values("issue_date").reset_index(drop=True)


def load_ibm(path) -> pd.DataFrame:
    """IBM Late Payment Histories: customerID, invoiceNumber, InvoiceDate, DueDate, InvoiceAmount, SettledDate."""
    raw = pd.read_csv(path, dtype=str)
    date = lambda c: pd.to_datetime(raw[c], format="mixed", dayfirst=False, errors="coerce")
    df = pd.DataFrame({"invoice_id": raw["invoiceNumber"], "customer_id": raw["customerID"],
                       "customer_name": raw["customerID"], "issue_date": date("InvoiceDate"),
                       "due_date": date("DueDate"), "amount": pd.to_numeric(raw["InvoiceAmount"], errors="coerce"),
                       "paid_date": date("SettledDate")})
    return _finish(df)


def load_payment_date(path, max_per_customer: int | None = 50) -> pd.DataFrame:
    """Payment Date Dataset: cust_number, invoice_id/doc_id, posting_date, due_in_date (YYYYMMDD),
    total_open_amount, clear_date. Makaledeki gibi müşteri başına en fazla `max_per_customer` fatura."""
    raw = pd.read_csv(path, dtype=str)
    ymd = lambda c: pd.to_datetime(raw[c].str.replace(r"\.0$", "", regex=True), format="%Y%m%d", errors="coerce")
    invoice = raw["invoice_id"] if "invoice_id" in raw else raw["doc_id"]
    df = pd.DataFrame({"invoice_id": invoice.fillna(raw.get("doc_id")).str.replace(r"\.0$", "", regex=True),
                       "customer_id": raw["cust_number"], "customer_name": raw.get("name_customer", raw["cust_number"]),
                       "issue_date": pd.to_datetime(raw["posting_date"], errors="coerce"), "due_date": ymd("due_in_date"),
                       "amount": pd.to_numeric(raw["total_open_amount"], errors="coerce"),
                       "paid_date": pd.to_datetime(raw["clear_date"], errors="coerce")})
    df = _finish(df)
    if max_per_customer:
        df = df.groupby("customer_id", group_keys=False).tail(max_per_customer).reset_index(drop=True)
    return df


def delay_study(obs: pd.DataFrame, origins: int = 6, step: int = 60, mature_days: int = 60) -> pd.DataFrame:
    """Geçmiş tarihlerde, o gün bilinenle model kurup henüz vadesi gelmemiş açık faturaların gecikmesini
    tahmin eder; modeli basit yöntemlerle karşılaştırır. Satır başına bir tahmin tarihi.

    Basit yöntemler (her biri müşterinin o güne kadar ödenmiş faturalarından):
    vade = 0 gün gecikme; medyan = geçmiş gecikmelerin medyanı; son2 / son4 = son 2 / 4 faturanın
    gecikme ortalaması (Małkus vd. hareketli ortalama özelliklerinin basit yöntem olarak kullanımı)."""
    end = obs[["issue_date", "paid_date"]].max().max()
    rows = []
    for k in range(1, origins + 1):
        t = end - pd.Timedelta(days=90 + k * step)
        past = censor(obs, t)
        X, y = training_frame(past, t)
        if len(X) < 60:
            break
        test = past[past["paid_date"].isna() & (past["due_date"] > t) & (past["due_date"] <= end - pd.Timedelta(days=mature_days))]
        outcome = obs.loc[test.index]
        test = test[outcome["paid_date"].notna()]                      # açık verilerde ödenmemiş fatura çok az
        if len(test) < 20:
            continue
        actual = (obs.loc[test.index, "paid_date"] - test["due_date"]).dt.days.to_numpy(float)
        Q = fit_model(X, y).predict(build_features(past, ref=t).loc[test.index])

        hist = past.dropna(subset=["paid_date"]).sort_values("paid_date")
        hist_delay = (hist["paid_date"] - hist["due_date"]).dt.days
        overall = float(hist_delay.median()) if len(hist_delay) else 0.0
        by = hist_delay.groupby(hist["customer_id"])
        base = {"vade": np.zeros(len(test)),
                "medyan": test["customer_id"].map(by.median()).fillna(overall).to_numpy(float),
                "son2": test["customer_id"].map(by.apply(lambda s: s.tail(2).mean())).fillna(overall).to_numpy(float),
                "son4": test["customer_id"].map(by.apply(lambda s: s.tail(4).mean())).fillna(overall).to_numpy(float)}
        pinball = np.mean([np.mean(np.maximum(q * (actual - Q[:, i]), (q - 1) * (actual - Q[:, i]))) for i, q in enumerate(QS)])
        row = {"tahmin_tarihi": t.date(), "fatura": len(test), "mae_model": float(np.mean(np.abs(actual - Q[:, 2]))),
               "kapsama_p10_p90": float(np.mean((actual >= Q[:, 0]) & (actual <= Q[:, -1]))), "pinball": float(pinball)}
        row |= {f"mae_{name}": float(np.mean(np.abs(actual - pred))) for name, pred in base.items()}
        rows.append(row)
    return pd.DataFrame(rows)


def run(dataset: str, path) -> dict:
    """Bir açık veri setinde fatura ve kasa (tahsilat) düzeyinde tam değerlendirme."""
    obs = load_ibm(path) if dataset == "ibm" else load_payment_date(path)
    end = obs[["issue_date", "paid_date"]].max().max()
    return {"veri": dataset, "fatura": len(obs), "müşteri": obs["customer_id"].nunique(),
            "aralık": (obs["issue_date"].min().date(), end.date()),
            "gecikme": delay_study(obs), "tahsilat": backtest_own(obs, end, origins=6)}


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    pd.set_option("display.width", 200)
    for name, file in (("ibm", "data/acik/ibm_late_payment.csv"), ("payment_date", "data/acik/payment_date.csv")):
        if not Path(file).exists():
            print(f"{file} yok; atlanıyor.")
            continue
        r = run(name, file)
        print(f"\n=== {r['veri']}: {r['fatura']} fatura, {r['müşteri']} müşteri, {r['aralık'][0]} – {r['aralık'][1]}")
        print("Fatura düzeyinde gecikme (gün; düşük iyi):")
        print(r["gecikme"].round(2).to_string(index=False))
        if r["tahsilat"] is not None:
            print("Kasa düzeyinde 90 günlük tahsilat (sapma %):")
            print(r["tahsilat"][["origin", "err_p50_pct", "err_due_pct", "err_median_pct", "inside"]].round(1).to_string(index=False))
