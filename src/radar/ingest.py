"""Kullanıcı dosyalarını (CSV / Excel / UBL-TR XML) standart tablolara çevirir.

Muhasebe programlarının dışa aktarımları farklı başlıklar, Türkçe sayı biçimi
(1.234,56) ve gün-ay-yıl tarihleri kullanır; burada hepsi tek biçime indirilir ve
düşürülen ya da varsayımla doldurulan her şey `notes` listesinde raporlanır.
"""
from __future__ import annotations

import io
import re

import numpy as np
import pandas as pd

from .ubl import parse_invoice

_TR = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")

ALIASES = {
    "invoice_id": ["fatura no", "fatura numarasi", "belge no", "evrak no", "invoice id", "no"],
    "customer_name": ["musteri", "cari", "cari adi", "cari unvan", "unvan", "musteri adi", "alici", "firma"],
    "vkn": ["vkn", "vergi no", "vkn tckn", "vergi numarasi", "vergi kimlik no"],
    "issue_date": ["fatura tarihi", "duzenleme tarihi", "belge tarihi", "tarih", "islem tarihi"],
    "due_date": ["vade", "vade tarihi", "odeme vadesi"],
    "amount": ["tutar", "genel toplam", "odenecek tutar", "toplam", "fatura tutari", "islem tutari", "alacak"],
    "paid_date": ["odeme tarihi", "tahsilat tarihi", "kapanis tarihi"],
    "open_amount": ["kalan", "acik tutar", "bakiye", "kalan tutar"],
    "description": ["aciklama", "islem aciklamasi", "detay"],
    "label": ["kalem", "gider", "aciklama", "tur"],
    "drawer": ["kesideci", "cek sahibi", "borclu", "musteri", "cari"],
}


def _key(s) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(s).translate(_TR).lower()).strip()


def _read(file) -> pd.DataFrame:
    name = str(getattr(file, "name", file)).lower()
    if name.endswith((".xlsx", ".xls")):
        return pd.read_excel(file, dtype=str)
    raw = file.read() if hasattr(file, "read") else open(file, "rb").read()
    for enc in ("utf-8-sig", "cp1254"):
        try:
            return pd.read_csv(io.StringIO(raw.decode(enc)), sep=None, engine="python", dtype=str)
        except UnicodeDecodeError:
            continue
    raise ValueError("Dosya okunamadı: desteklenen biçimler CSV ve Excel.")


def _pick(df: pd.DataFrame, fields: list[str], required: list[str]) -> pd.DataFrame:
    cols = {_key(c): c for c in df.columns}
    out = pd.DataFrame(index=df.index)
    for f in fields:
        src = next((cols[a] for a in [_key(f)] + ALIASES[f] if a in cols), None)
        if src is not None:
            out[f] = df[src]
    missing = [f for f in required if f not in out]
    if missing:
        raise ValueError(f"Eksik sütun: {', '.join(missing)}. Bulunan başlıklar: {', '.join(map(str, df.columns))}")
    return out


def _num(s: pd.Series) -> pd.Series:
    def one(v):
        if v is None or (isinstance(v, float) and np.isnan(v)):
            return np.nan
        t = re.sub(r"[^\d,.\-]", "", str(v))
        if "," in t and "." in t:
            t = t.replace(".", "").replace(",", ".") if t.rfind(",") > t.rfind(".") else t.replace(",", "")
        elif "," in t:
            t = t.replace(",", ".")
        try:
            return float(t)
        except ValueError:
            return np.nan
    return s.map(one)


def _date(s: pd.Series) -> pd.Series:
    iso = pd.to_datetime(s, format="ISO8601", errors="coerce")
    return iso.fillna(pd.to_datetime(s, dayfirst=True, errors="coerce")).dt.normalize()


def _finish_invoices(df: pd.DataFrame, default_terms: int, notes: list[str]) -> pd.DataFrame:
    n = len(df)
    df = df.dropna(subset=["invoice_id", "issue_date", "amount"])
    df = df[df["amount"] > 0].drop_duplicates("invoice_id")
    if len(df) < n:
        notes.append(f"{n - len(df)} satır atlandı (eksik numara/tarih/tutar, sıfır veya negatif tutar, yinelenen fatura).")
    for col in ("vkn", "customer_name"):
        if col not in df:
            df[col] = None
    df["vkn"] = df["vkn"].astype("string").str.replace(r"\D", "", regex=True).replace("", pd.NA)
    df["customer_name"] = df["customer_name"].fillna(df["vkn"]).fillna("Bilinmeyen")
    df["customer_id"] = df["vkn"].fillna(df["customer_name"].map(_key))
    df["vkn"] = df["vkn"].fillna("")
    if "due_date" not in df:
        df["due_date"] = pd.NaT
    no_due = df["due_date"].isna()
    if no_due.any():
        df.loc[no_due, "due_date"] = df.loc[no_due, "issue_date"] + pd.Timedelta(days=default_terms)
        notes.append(f"{int(no_due.sum())} faturada vade tarihi yoktu; fatura tarihi + {default_terms} gün varsayıldı.")
    if "paid_date" not in df:
        df["paid_date"] = pd.NaT
    if "open_amount" not in df:
        df["open_amount"] = np.where(df["paid_date"].isna(), df["amount"], 0.0)
    df["open_amount"] = df["open_amount"].fillna(df["amount"]).clip(lower=0)
    cols = ["invoice_id", "customer_id", "customer_name", "vkn", "issue_date", "due_date", "amount", "paid_date", "open_amount"]
    return df[cols].sort_values("issue_date").reset_index(drop=True)


def load_invoices(file, default_terms: int = 30):
    """Kesilen faturalar. Zorunlu: fatura no, müşteri, fatura tarihi, tutar."""
    notes: list[str] = []
    df = _pick(_read(file), ["invoice_id", "customer_name", "vkn", "issue_date", "due_date", "amount",
                             "paid_date", "open_amount"], ["invoice_id", "customer_name", "issue_date", "amount"])
    for c in ("issue_date", "due_date", "paid_date"):
        if c in df:
            df[c] = _date(df[c])
    for c in ("amount", "open_amount"):
        if c in df:
            df[c] = _num(df[c])
    return _finish_invoices(df, default_terms, notes), notes


def load_ubl(files, default_terms: int = 30):
    """UBL-TR XML dosyaları (dosya nesneleri veya bayt dizileri)."""
    notes, rows = [], []
    for f in files:
        try:
            rows.append(parse_invoice(f.read() if hasattr(f, "read") else f))
        except Exception:
            notes.append(f"{getattr(f, 'name', 'XML')} okunamadı.")
    df = pd.DataFrame(rows).drop(columns=["due_source", "currency"], errors="ignore")
    if df.empty:
        return df, notes
    df["due_date"] = pd.to_datetime(df["due_date"])
    return _finish_invoices(df, default_terms, notes), notes


def load_payments(file):
    """Banka ekstresi. Zorunlu: tarih, tutar, açıklama. Yalnızca hesaba girişler alınır."""
    notes: list[str] = []
    df = _pick(_read(file), ["issue_date", "amount", "description"], ["issue_date", "amount", "description"])
    df = pd.DataFrame({"date": _date(df["issue_date"]), "amount": _num(df["amount"]),
                       "description": df["description"].fillna("")})
    n = len(df)
    df = df.dropna(subset=["date", "amount"])
    df = df[df["amount"] > 0]
    if len(df) < n:
        notes.append(f"Ekstrede {n - len(df)} satır atlandı (çıkış hareketi ya da okunamayan tarih/tutar).")
    return df.reset_index(drop=True), notes


def load_schedule(file, label_field: str = "label"):
    """Tarih + tutar listesi: planlı giderler (label) veya çek/senet portföyü (drawer)."""
    df = _pick(_read(file), ["due_date", "issue_date", "amount", label_field], ["amount"])
    date = df["due_date"] if "due_date" in df else df.get("issue_date")
    if date is None:
        raise ValueError("Eksik sütun: tarih veya vade.")
    out = pd.DataFrame({"date": _date(date), "amount": _num(df["amount"]),
                        "label": df[label_field] if label_field in df else ""})
    return out.dropna(subset=["date", "amount"]).query("amount > 0").reset_index(drop=True)
