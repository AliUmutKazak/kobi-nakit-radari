"""Tahsilat önceliklendirme, mesaj taslakları ve temel alacak metrikleri.

Mesajlar yalnızca TASLAKTIR; hiçbir şey kullanıcı onayı olmadan gönderilmez. Resmî
bildirim tonundaki taslaklar ayrıca hukukçu kontrolü notu taşır.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# TTK m.1530 kapsamında TCMB'nin 2026 için ilan ettiği değerler (her yıl güncellenir).
LATE_INTEREST_RATE = 0.43
MIN_RECOVERY_COST_TL = 2020


def metrics(obs: pd.DataFrame, as_of) -> dict:
    as_of = pd.Timestamp(as_of)
    open_inv = obs[obs["open_amount"] > 0]
    overdue = open_inv[open_inv["due_date"] < as_of]
    sales_90 = obs.loc[obs["issue_date"] > as_of - pd.Timedelta(days=90), "amount"].sum()
    paid = obs[obs["paid_date"] > as_of - pd.Timedelta(days=180)]
    dbt = (paid["paid_date"] - paid["due_date"]).dt.days
    return {
        "open_ar": float(open_inv["open_amount"].sum()),
        "overdue_ar": float(overdue["open_amount"].sum()),
        "dso": float(open_inv["open_amount"].sum() / sales_90 * 90) if sales_90 else float("nan"),
        "avg_days_beyond_terms": float(np.average(dbt, weights=paid["amount"])) if len(paid) else float("nan"),
        "on_time_rate": float((dbt <= 0).mean()) if len(paid) else float("nan"),
    }


def prioritize(open_inv: pd.DataFrame, pay_day: np.ndarray, as_of, gap_day: int) -> pd.DataFrame:
    """Faturaları "açık gününe kadar tahsil edilememe riski taşıyan tutar"a göre sıralar."""
    as_of = pd.Timestamp(as_of)
    df = open_inv[["invoice_id", "customer_id", "customer_name", "due_date", "open_amount"]].copy()
    df["days_overdue"] = (as_of - df["due_date"]).dt.days
    df["p_late"] = (pay_day > gap_day).mean(axis=1)
    df["expected_pay_day"] = np.median(pay_day, axis=1)
    df["amount_at_risk"] = df["open_amount"] * df["p_late"]
    df["stage"] = pd.cut(df["days_overdue"], [-np.inf, -8, 0, 15, np.inf],
                         labels=["bekle", "hatirlatma", "mutabakat", "resmi"]).astype(str)
    # Vadesine bir haftadan fazla olan faturalar için hatırlatma işe yaramaz; listede sona alınır.
    df["actionable"] = df["stage"] != "bekle"
    return df.sort_values(["actionable", "amount_at_risk"], ascending=False).reset_index(drop=True)


def _tl(x: float) -> str:
    return f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " TL"


def draft_message(row, seller: str, on_time_rate: float | None = None) -> dict | None:
    """Aşamaya göre WhatsApp/e-posta taslağı üretir. Tanıtım içeriği eklenmez."""
    due, amount = pd.Timestamp(row["due_date"]).strftime("%d.%m.%Y"), _tl(row["open_amount"])
    ref = f"{row['invoice_id']} numaralı, {amount} tutarındaki faturamız"
    if row["stage"] == "bekle":
        return None
    if row["stage"] == "hatirlatma":
        habit = (" Bugüne kadarki ödemelerinizin büyük bölümünü vadesinde yaptığınız için teşekkür ederiz."
                 if on_time_rate is not None and on_time_rate >= 0.7 else "")
        body = (f"Merhaba, {ref} için vade tarihi {due}.{habit} "
                f"Ödeme planınızda bir değişiklik varsa bize bildirmeniz yeterli. {seller}")
        note = None
    elif row["stage"] == "mutabakat":
        body = (f"Merhaba, {ref} {due} tarihinde vadesini doldurdu ve kayıtlarımızda açık görünüyor. "
                f"Ödeme yapıldıysa dekontu, eksik bir belge (irsaliye, sipariş onayı) varsa bilgisini "
                f"paylaşabilir misiniz? Kayıtlarımızı birlikte kontrol edelim. {seller}")
        note = None
    else:
        body = (f"Sayın yetkili, {ref} {due} vadesinden bu yana {int(row['days_overdue'])} gündür ödenmemiştir. "
                f"Ödemenin yapılmasını veya ödeme tarihinin yazılı olarak bildirilmesini rica ederiz. "
                f"Türk Ticaret Kanunu m.1530 uyarınca geç ödemelerde gecikme faizi "
                f"(2026 için yıllık %{LATE_INTEREST_RATE * 100:.0f}) ve en az {_tl(MIN_RECOVERY_COST_TL)} "
                f"tahsil gideri talep hakkımız saklıdır. {seller}")
        note = "Resmî bildirim: göndermeden önce sözleşme koşulları ve hukukçu görüşüyle teyit edin."
    return {"invoice_id": row["invoice_id"], "customer_name": row["customer_name"], "stage": row["stage"],
            "subject": f"{row['invoice_id']} numaralı fatura hakkında", "body": body,
            "requires_approval": True, "note": note}
