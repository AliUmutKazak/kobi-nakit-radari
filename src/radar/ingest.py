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
    "invoice_id": ["fatura no", "fatura numarasi", "belge no", "belge numarasi", "evrak no", "evrak numarasi",
                   "invoice id", "no"],
    "customer_name": ["musteri", "cari", "cari adi", "cari unvan", "cari unvani", "cari ismi", "unvan", "musteri adi",
                      "musteri unvani", "hesap adi", "alici", "firma"],
    "vkn": ["vkn", "vergi no", "vkn tckn", "vergi no tckn", "tckn", "vergi numarasi", "vergi kimlik no"],
    "issue_date": ["fatura tarihi", "duzenleme tarihi", "belge tarihi", "evrak tarihi", "tarih", "islem tarihi",
                   "tarih saat", "fis tarihi"],
    "due_date": ["vade", "vade tarihi", "odeme vadesi"],
    "amount": ["tutar", "genel toplam", "odenecek tutar", "toplam", "fatura tutari", "islem tutari", "alacak"],
    "paid_date": ["odeme tarihi", "tahsilat tarihi", "kapanis tarihi"],
    "open_amount": ["kalan", "acik tutar", "bakiye", "kalan tutar", "kalan meblag"],
    "phone": ["telefon", "cep", "cep telefonu", "gsm", "whatsapp", "tel", "musteri telefon"],
    "direction": ["b a", "borc alacak", "yon", "islem yonu"],
    "status": ["durum", "cek durumu", "statu", "son durum"],
    "disputed": ["itiraz", "itirazli", "ihtilafli", "anlasmazlik"],
    "email": ["e posta", "eposta", "email", "mail", "e mail", "musteri e posta"],
    "currency": ["para birimi", "doviz", "doviz cinsi", "doviz turu", "pb"],
    "invoice_type": ["fatura tipi", "fatura turu", "belge tipi"],
    "promised_date": ["odeme sozu", "soz tarihi", "odeme sozu tarihi", "taahhut tarihi"],
    "description": ["aciklama", "islem aciklamasi", "detay"],
    "label": ["kalem", "gider", "aciklama", "tur"],
    "drawer": ["kesideci", "cek sahibi", "borclu", "musteri", "cari"],
    "supplier": ["tedarikci", "satici", "tedarikci unvan", "cari", "cari unvan", "firma", "unvan"],
}


FIELD_LABELS = {"invoice_id": "Fatura no", "customer_name": "Müşteri / cari unvan", "issue_date": "Tarih",
                "amount": "Tutar", "due_date": "Vade tarihi", "vkn": "VKN / TCKN", "paid_date": "Ödeme tarihi",
                "open_amount": "Kalan tutar", "description": "Açıklama", "email": "Müşteri e-postası"}
INVOICE_FIELDS = ["invoice_id", "customer_name", "issue_date", "amount", "due_date", "vkn", "paid_date", "open_amount",
                  "email"]
INVOICE_REQUIRED = ["invoice_id", "customer_name", "issue_date", "amount"]
PAYMENT_FIELDS = PAYMENT_REQUIRED = ["issue_date", "amount", "description"]


def _key(s) -> str:
    key = re.sub(r"[^a-z0-9]+", " ", str(s).translate(_TR).lower()).strip()
    return re.sub(r"( tl| try)+$", "", key)            # "Tutar (TL)" ile "Tutar" aynı alan


def _known(cell) -> bool:
    return any(_key(cell) in names or _key(cell) == field for field, names in ALIASES.items())


def _fix_header(df: pd.DataFrame, scan: int = 25) -> pd.DataFrame:
    """Banka ve muhasebe dışa aktarımlarında tablo çoğu zaman birkaç satır hesap/dönem bilgisinden
    sonra başlar. Başlık, bilinen sütun adlarından en az ikisini içeren ilk satır sayılır."""
    if sum(_known(c) for c in df.columns) >= 2:
        return df
    for i in range(min(scan, len(df))):
        row = df.iloc[i]
        if sum(_known(v) for v in row if isinstance(v, str)) >= 2:
            body = df.iloc[i + 1:].copy()
            body.columns = [str(v) if isinstance(v, str) and v.strip() else f"sutun_{j}" for j, v in enumerate(row)]
            return body.dropna(how="all").reset_index(drop=True)
    return df


def _read(file) -> pd.DataFrame:
    name = str(getattr(file, "name", file)).lower()
    if name.endswith((".xlsx", ".xls")):
        return _fix_header(pd.read_excel(file, dtype=str))
    raw = file.read() if hasattr(file, "read") else open(file, "rb").read()
    for enc in ("utf-8-sig", "cp1254"):
        try:
            text = raw.decode(enc)
            # Başlıktan önceki bilgi satırları farklı sayıda sütun içerebilir; ayraç başlık satırından bulunur.
            lines = text.splitlines()
            start = next((i for i, line in enumerate(lines[:25])
                          if sum(_known(c) for c in re.split(r"[;,\t]", line)) >= 2), 0)
            return _fix_header(pd.read_csv(io.StringIO("\n".join(lines[start:])), sep=None, engine="python", dtype=str))
        except UnicodeDecodeError:
            continue
    raise ValueError("Dosya okunamadı: desteklenen biçimler CSV ve Excel.")


def columns(file) -> list[str]:
    """Dosyadaki sütun başlıkları (elle eşleştirme ekranı için)."""
    return [str(c) for c in _read(file).columns]


def _pick(df: pd.DataFrame, fields: list[str], required: list[str], mapping: dict | None = None) -> pd.DataFrame:
    """Sütunları standart adlara çevirir; `mapping` (alan -> dosyadaki başlık) otomatik tanımanın önüne geçer."""
    cols = {_key(c): c for c in df.columns}
    out = pd.DataFrame(index=df.index)
    for f in fields:
        src = (mapping or {}).get(f)
        if src not in df.columns:
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
        elif re.fullmatch(r"-?\d{1,3}(\.\d{3})+", t):
            t = t.replace(".", "")          # "200.000": Türkçe binlik ayracı, ondalık değil
        try:
            return float(t)
        except ValueError:
            return np.nan
    return s.map(one)


def _date(s: pd.Series) -> pd.Series:
    iso = pd.to_datetime(s, format="ISO8601", errors="coerce")
    return iso.fillna(pd.to_datetime(s, dayfirst=True, errors="coerce")).dt.normalize()


def normalize_phone(value) -> str:
    """Türkiye cep numarasını uluslararası biçime (905XXXXXXXXX) çevirir; tanınmazsa boş döner."""
    digits = re.sub(r"\D", "", str(value or ""))
    if len(digits) == 10 and digits.startswith("5"):
        digits = "90" + digits
    elif len(digits) == 11 and digits.startswith("05"):
        digits = "9" + digits
    return digits if len(digits) == 12 and digits.startswith("905") else ""


def parse_rates(text: str) -> dict[str, float]:
    """"USD=41,50; EUR=48,2" biçimindeki kur girişini sözlüğe çevirir; okunamayan parçalar atlanır."""
    rates = {}
    for part in re.split(r"[;\n]+", text or ""):
        code, _, value = part.partition("=")
        number = _num(pd.Series([value])).iloc[0]
        if code.strip() and number == number and number > 0:
            rates[code.strip().upper()] = float(number)
    return rates


def _finish_invoices(df: pd.DataFrame, default_terms: int, notes: list[str],
                     rates: dict[str, float] | None = None) -> pd.DataFrame:
    df = df.copy()
    # Dövizli fatura, kullanıcının girdiği kurla TL'ye çevrilir; kuru girilmemiş döviz TL ile
    # sessizce toplanmaz, dışarıda bırakılıp bildirilir.
    code = (df["currency"].fillna("TRY").astype(str).str.strip().str.upper().replace({"TL": "TRY", "": "TRY", "₺": "TRY"})
            if "currency" in df else pd.Series("TRY", index=df.index))
    df["currency"] = code
    rate = code.map({"TRY": 1.0} | (rates or {}))
    if rate.isna().any():
        kinds = ", ".join(sorted(code[rate.isna()].unique()))
        notes.append(f"{int(rate.isna().sum())} dövizli fatura ({kinds}) dışarıda bırakıldı; "
                     "tahmine katmak için bu dövizlerin kurunu girin.")
    converted = (code != "TRY") & rate.notna()
    if converted.any():
        used = ", ".join(f"{c} = {rates[c]:g}" for c in sorted(code[converted].unique()))
        notes.append(f"{int(converted.sum())} dövizli fatura girilen kurla TL'ye çevrildi ({used}). "
                     "Kur değişimi tahmin bandına dahil değildir.")
    for col in ("amount", "open_amount"):
        if col in df:
            df[col] = df[col] * rate
    df = df[rate.notna()]

    for col in ("vkn", "customer_name"):
        if col not in df:
            df[col] = None
    df["vkn"] = df["vkn"].astype("string").str.replace(r"\D", "", regex=True).replace("", pd.NA)
    df["customer_name"] = df["customer_name"].fillna(df["vkn"]).fillna("Bilinmeyen")
    df["customer_id"] = df["vkn"].fillna(df["customer_name"].map(_key))
    df["vkn"] = df["vkn"].fillna("")

    is_refund = (df["invoice_type"].map(_key).str.contains("iade", na=False) if "invoice_type" in df
                 else pd.Series(False, index=df.index))
    refunds, df = df[is_refund], df[~is_refund]

    n = len(df)
    df = df.dropna(subset=["invoice_id", "issue_date", "amount"])
    df = df[df["amount"] > 0].drop_duplicates("invoice_id")
    if len(df) < n:
        notes.append(f"{n - len(df)} satır atlandı (eksik numara/tarih/tutar, sıfır veya negatif tutar, yinelenen fatura).")
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

    # İade faturası alacak değildir: aynı müşterinin en eski açık faturalarından düşülür.
    applied = leftover = 0.0
    for r in refunds.dropna(subset=["amount"]).itertuples():
        remaining = abs(float(r.amount))
        for idx in df[(df["customer_id"] == r.customer_id) & (df["open_amount"] > 0)].sort_values("due_date").index:
            take = min(remaining, df.at[idx, "open_amount"])
            df.at[idx, "open_amount"] -= take
            remaining -= take
            if remaining <= 0.005:
                break
        applied += abs(float(r.amount)) - remaining
        leftover += remaining
    if applied:
        notes.append(f"{len(refunds)} iade faturasından {applied:,.2f} TL, ilgili müşterilerin en eski açık faturalarından düşüldü.")
    if leftover > 0.005:
        notes.append(f"{leftover:,.2f} TL tutarında iade için düşülecek açık fatura bulunamadı; müşteriye borcunuz olabilir.")

    df["disputed"] = (df["disputed"].map(lambda v: _key(v) in {"evet", "e", "x", "1", "true", "var", "itirazli"})
                      if "disputed" in df else False)
    if "promised_date" not in df:
        df["promised_date"] = pd.NaT
    df["email"] = df["email"].fillna("").astype(str).str.strip() if "email" in df else ""
    df["phone"] = df["phone"].map(normalize_phone) if "phone" in df else ""
    cols = ["invoice_id", "customer_id", "customer_name", "vkn", "issue_date", "due_date", "amount", "paid_date",
            "open_amount", "disputed", "promised_date", "currency", "email", "phone"]
    return df[cols].sort_values("issue_date").reset_index(drop=True)


def load_invoices(file, default_terms: int = 30, mapping: dict | None = None, rates: dict | None = None):
    """Kesilen faturalar. Zorunlu: fatura no, müşteri, fatura tarihi, tutar."""
    notes: list[str] = []
    raw = _read(file)
    keys = {_key(c): c for c in raw.columns}
    if "evrak seri" in keys and "evrak sira" in keys and not any(k in keys for k in ALIASES["invoice_id"]):
        # Mikro: fatura numarası seri ve sıra olarak iki sütunda gelir.
        raw["Fatura No"] = raw[keys["evrak seri"]].fillna("").str.strip() + raw[keys["evrak sira"]].fillna("").str.strip()
    df = _pick(raw, ["invoice_id", "customer_name", "vkn", "issue_date", "due_date", "amount",
                             "paid_date", "open_amount", "disputed", "promised_date", "currency", "invoice_type",
                             "email", "phone"],
               INVOICE_REQUIRED, mapping)
    for c in ("issue_date", "due_date", "paid_date", "promised_date"):
        if c in df:
            df[c] = _date(df[c])
    for c in ("amount", "open_amount"):
        if c in df:
            df[c] = _num(df[c])
    return _finish_invoices(df, default_terms, notes, rates), notes


def load_ubl(files, default_terms: int = 30, rates: dict | None = None):
    """UBL-TR XML dosyaları (dosya nesneleri veya bayt dizileri)."""
    notes, rows = [], []
    for f in files:
        try:
            rows.append(parse_invoice(f.read() if hasattr(f, "read") else f))
        except Exception:
            notes.append(f"{getattr(f, 'name', 'XML')} okunamadı.")
    df = pd.DataFrame(rows).drop(columns=["due_source"], errors="ignore")
    if df.empty:
        return df, notes
    df["due_date"] = pd.to_datetime(df["due_date"])
    return _finish_invoices(df, default_terms, notes, rates), notes


def load_payments(file, mapping: dict | None = None):
    """Banka ekstresi. Zorunlu: tarih, tutar, açıklama. Yalnızca hesaba girişler alınır."""
    notes: list[str] = []
    df = _pick(_read(file), PAYMENT_FIELDS + ["direction"], PAYMENT_REQUIRED, mapping)
    incoming = (df["direction"].map(_key).str.startswith("a", na=False) if "direction" in df
                else pd.Series(True, index=df.index))       # B/A sütunu varsa yalnızca "A" (alacak) girişlerdir
    df = pd.DataFrame({"date": _date(df["issue_date"]), "amount": _num(df["amount"]).abs().where(incoming),
                       "description": df["description"].fillna("")})
    n = len(df)
    df = df.dropna(subset=["date", "amount"])
    df = df[df["amount"] > 0]
    if len(df) < n:
        notes.append(f"Ekstrede {n - len(df)} satır atlandı (çıkış hareketi ya da okunamayan tarih/tutar).")
    return df.reset_index(drop=True), notes


PAYABLES_LABEL = "Ödenecek faturalar"


def load_payables(file, default_terms: int = 30):
    """Tedarikçilerden gelen, henüz ödenmemiş faturalar. Zorunlu: tutar ve vade ya da fatura tarihi.

    Kalan tutar sütunu varsa o ödenir; vade yoksa fatura tarihi + `default_terms` gün varsayılır."""
    notes: list[str] = []
    df = _pick(_read(file), ["invoice_id", "supplier", "due_date", "issue_date", "amount", "open_amount"], ["amount"])
    due = _date(df["due_date"]) if "due_date" in df else pd.Series(pd.NaT, index=df.index)
    if "issue_date" in df:
        missing = due.isna() & _date(df["issue_date"]).notna()
        if missing.any():
            due[missing] = _date(df["issue_date"])[missing] + pd.Timedelta(days=default_terms)
            notes.append(f"{int(missing.sum())} borç faturasında vade yoktu; fatura tarihi + {default_terms} gün varsayıldı.")
    amount = _num(df["open_amount"]).fillna(_num(df["amount"])) if "open_amount" in df else _num(df["amount"])
    out = pd.DataFrame({"date": due, "amount": amount, "label": PAYABLES_LABEL,
                        "supplier": df["supplier"] if "supplier" in df else "",
                        "invoice_id": df["invoice_id"] if "invoice_id" in df else ""})
    n = len(out)
    out = out.dropna(subset=["date", "amount"]).query("amount > 0").reset_index(drop=True)
    if len(out) < n:
        notes.append(f"{n - len(out)} borç satırı atlandı (tarih ya da tutar okunamadı, sıfır veya negatif tutar).")
    return out, notes


def payables_to_outflows(payables: pd.DataFrame, as_of) -> tuple[pd.DataFrame, list[str]]:
    """Borç faturalarını kasa çıkışına çevirir. Vadesi geçmiş borç ilk gün ödenecek sayılır:
    ertelenebileceği varsayımı kasayı olduğundan iyi gösterir."""
    as_of = pd.Timestamp(as_of)
    flows = payables[["date", "amount", "label"]].copy()
    late = flows["date"] <= as_of
    notes = []
    if late.any():
        notes.append(f"Vadesi geçmiş {flows.loc[late, 'amount'].sum():,.0f} TL borç, yarın ödenecek sayıldı.")
        flows.loc[late, "date"] = as_of + pd.Timedelta(days=1)
    return flows, notes


CHEQUE_EXCLUDED = ("ciro", "iskonto", "faktoring", "tahsil edildi", "odendi", "karsiliksiz", "iade")


def load_cheques(file):
    """Alınan çek/senet portföyü. Durum sütunu varsa cirolanmış, iskontoya/faktoringe verilmiş ya da
    sonuçlanmış evrak kasaya giriş sayılmaz: ciro edilen çekin parası bize değil tedarikçiye gelir."""
    df = _pick(_read(file), ["due_date", "issue_date", "amount", "drawer", "status"], ["amount"])
    date = df["due_date"] if "due_date" in df else df.get("issue_date")
    if date is None:
        raise ValueError("Eksik sütun: tarih veya vade.")
    out = pd.DataFrame({"date": _date(date), "amount": _num(df["amount"]),
                        "label": df["drawer"] if "drawer" in df else "",
                        "status": df["status"].fillna("") if "status" in df else ""})
    out = out.dropna(subset=["date", "amount"]).query("amount > 0")
    gone = out["status"].map(_key).map(lambda s: any(w in s for w in CHEQUE_EXCLUDED))
    notes = []
    if gone.any():
        notes.append(f"{int(gone.sum())} çek/senet ({out.loc[gone, 'amount'].sum():,.0f} TL) cirolanmış, iskontoya verilmiş "
                     "ya da sonuçlanmış olduğu için tahmine katılmadı. Ciro edilen çek karşılıksız çıkarsa "
                     "tedarikçiye karşı sorumluluğunuz sürer.")
    return out[~gone].drop(columns="status").reset_index(drop=True), notes


# Vergi takvimi (GİB): muhtasar ve prim hizmet beyannamesi ödemesi izleyen ayın 26'sı, KDV 28'i.
# SGK primi: izleyen ayın son günü. Son gün hafta sonuna denk gelirse ilk iş gününe kayar
# (resmî tatiller dahil değil).
def fixed_cost_plan(as_of, horizon: int = 90, payroll: float = 0.0, payroll_day: int = 1, muhtasar: float = 0.0,
                    sgk: float = 0.0, kdv: float = 0.0, rent: float = 0.0, rent_day: int = 1) -> pd.DataFrame:
    """Dosyası olmayan kullanıcı için aylık sabit giderlerden kasa çıkışı üretir."""
    as_of = pd.Timestamp(as_of)
    end = as_of + pd.Timedelta(days=horizon)
    rows = []
    for month in pd.period_range(as_of, end, freq="M"):
        first = month.to_timestamp()
        for label, amount, day in (("Maaş", payroll, payroll_day), ("Muhtasar", muhtasar, 26), ("KDV", kdv, 28),
                                   ("Kira", rent, rent_day), ("SGK primi", sgk, month.days_in_month)):
            if amount <= 0:
                continue
            date = first + pd.Timedelta(days=min(day, month.days_in_month) - 1)
            if label in ("Muhtasar", "KDV", "SGK primi"):
                while date.dayofweek >= 5:
                    date += pd.Timedelta(days=1)
            if as_of < date <= end:
                rows.append((date, float(amount), label))
    return pd.DataFrame(rows, columns=["date", "amount", "label"]).sort_values("date").reset_index(drop=True)


def load_schedule(file, label_field: str = "label"):
    """Tarih + tutar listesi: planlı giderler (label) veya çek/senet portföyü (drawer)."""
    df = _pick(_read(file), ["due_date", "issue_date", "amount", label_field], ["amount"])
    date = df["due_date"] if "due_date" in df else df.get("issue_date")
    if date is None:
        raise ValueError("Eksik sütun: tarih veya vade.")
    out = pd.DataFrame({"date": _date(date), "amount": _num(df["amount"]),
                        "label": df[label_field] if label_field in df else ""})
    return out.dropna(subset=["date", "amount"]).query("amount > 0").reset_index(drop=True)
