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
    "debit": ["borc", "borc tutari", "cikis", "cikan tutar", "giden"],
    "balance": ["bakiye", "bakiye tl", "hesap bakiyesi", "kalan bakiye"],
    "status": ["durum", "cek durumu", "statu", "son durum"],
    "disputed": ["itiraz", "itirazli", "ihtilafli", "anlasmazlik"],
    "email": ["e posta", "eposta", "email", "mail", "e mail", "musteri e posta"],
    "currency": ["para birimi", "doviz", "doviz cinsi", "doviz turu", "pb"],
    "invoice_type": ["fatura tipi", "fatura turu", "belge tipi"],
    "promised_date": ["odeme sozu", "soz tarihi", "odeme sozu tarihi", "taahhut tarihi"],
    "description": ["aciklama", "islem aciklamasi", "aciklama islem turu", "detay", "islem turu"],
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
    code = (df["currency"].fillna("TRY").astype(str).str.strip().str.upper().replace({"TL": "TRY", "TRL": "TRY", "YTL": "TRY", "": "TRY", "₺": "TRY"})
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
    df["fx_rate"] = rate                 # orijinal tutar = TL tutarı / kur; kur senaryosu için saklanır
    df = df[rate.notna()]

    for col in ("vkn", "customer_name"):
        if col not in df:
            df[col] = None
    # Excel, 0 ile başlayan VKN'yi sayı sanıp baştaki sıfırı siler: 9 haneye düşmüş VKN tamamlanır.
    vkn = df["vkn"].astype("string").str.replace(r"\.0$", "", regex=True).str.replace(r"\D", "", regex=True)
    vkn = vkn.where(vkn.str.len() != 9, "0" + vkn)
    df["vkn"] = vkn.where(vkn.str.len().isin([10, 11]))
    # Luca muavininde hesap adı hesap koduyla başlar ("120.01.004 Marmara Kimya"); kod atılır.
    df["customer_name"] = df["customer_name"].astype("string").str.replace(r"^\s*\d{3}(?:\.\d{1,5})+\s*[-:]?\s*", "",
                                                                            regex=True)
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
            "open_amount", "disputed", "promised_date", "currency", "fx_rate", "email", "phone"]
    if "cheque_due" in df and df["cheque_due"].notna().any():
        cols.append("cheque_due")                 # çekle kapanan faturalarda çek vadesi (cari hesap ekstresinden)
    return df[cols].sort_values("issue_date").reset_index(drop=True)


def possible_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Olası mükerrer faturalar: aynı müşteri, aynı gün, aynı tutar, farklı numara.

    Aynı numara yüklemede zaten tekilleştirilir. Aynı faturanın farklı numarayla iki kez girilmesi (ör. elle ve
    e-faturadan) alacağı iki kez saydırır ve kasayı olduğundan dolu gösterir. Aynı gün aynı tutarda gerçekten iki
    fatura da kesilebileceği için kayıt silinmez; kullanıcıya gösterilir. Dönen: grup başına bir satır
    (customer_name, issue_date, amount, invoice_ids)."""
    key = df.assign(_day=pd.to_datetime(df["issue_date"]).dt.normalize(), _amt=df["amount"].round(2))
    g = key.groupby(["customer_id", "_day", "_amt"])
    out = g.agg(customer_name=("customer_name", "first"), n=("invoice_id", "nunique"),
                invoice_ids=("invoice_id", lambda x: ", ".join(map(str, sorted(set(x))))))
    out = out[out["n"] > 1].reset_index().rename(columns={"_day": "issue_date", "_amt": "amount"})
    return out[["customer_name", "issue_date", "amount", "n", "invoice_ids"]]


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


def _direction_from_balance(amount: pd.Series, balance: pd.Series) -> pd.Series | None:
    """Bakiye değişiminden hareketin yönü (+1 giriş, −1 çıkış, NaN bilinmiyor). Ekstre eskiden yeniye ya da
    yeniden eskiye sıralı olabilir; satırların en az %80'inde |bakiye farkı| = |tutar| tutan sıra seçilir."""
    a = amount.abs()
    best, best_hits = None, 0.0
    for diff in (balance.diff(), balance - balance.shift(-1)):
        hits = ((diff.abs() - a).abs() <= 0.005 * a + 0.5)
        rate = hits.sum() / max(int(diff.notna().sum()), 1)       # ilk/son satırın önceki bakiyesi yoktur
        if rate > best_hits:
            best, best_hits = np.sign(diff).where(hits), rate
    return best if best_hits >= 0.8 else None


def _last_balance(date: pd.Series, balance: pd.Series) -> tuple[pd.Timestamp, float] | None:
    """Ekstredeki en son bakiye ve tarihi. Ekstre eskiden yeniye sıralıysa son satır, yeniden eskiye sıralıysa ilk
    satır en yenidir (aynı gündeki hareketlerin sırası yalnızca dosya sırasından bilinir)."""
    ok = date.notna() & balance.notna()
    if not ok.any():
        return None
    d, b = date[ok], balance[ok]
    i = d.index[-1] if d.iloc[0] <= d.iloc[-1] else d.index[0]
    return d[i], float(b[i])


def bank_movements(file, mapping: dict | None = None, with_balance: bool = False):
    """Banka ekstresindeki girişler ve çıkışlar (date, amount, description; tutarlar pozitif) ve notlar.

    Yön sırayla şuradan çıkarılır: B/A (yön) sütunu; ayrı Borç ve Alacak sütunları; eksi işaretli tutar; bakiye
    değişimi. Hiçbiri yoksa bütün satırlar giriş sayılır ve kullanıcı uyarılır. Önceki sürüm işaretli tutarların
    mutlak değerini alıyordu: "−15.000" kira ödemesi tahsilat sayılıyordu (kasa olduğundan dolu görünür).

    with_balance=True ise dördüncü değer ekstredeki son bakiye ve tarihidir (bakiye sütunu yoksa None); panel bunu
    girilen kasa tutarının yanında gösterir."""
    notes: list[str] = []
    df = _pick(_read(file), PAYMENT_FIELDS + ["direction", "debit", "balance"], PAYMENT_REQUIRED, mapping)
    amt = _num(df["amount"])
    unknown = pd.Series(False, index=df.index)
    if "direction" in df:
        d = df["direction"].map(_key)
        inflow, outflow = amt.abs().where(d.str.startswith("a", na=False)), amt.abs().where(d.str.startswith("b", na=False))
    elif "debit" in df:                                       # ayrı Borç / Alacak sütunları
        inflow, outflow = amt.where(amt > 0), _num(df["debit"]).abs().where(lambda x: x > 0)
    elif (amt < 0).any():                                     # işaretli tutar
        inflow, outflow = amt.where(amt > 0), (-amt).where(amt < 0)
    else:
        sign = _direction_from_balance(amt, _num(df["balance"])) if "balance" in df else None
        if sign is not None:
            inflow, outflow = amt.abs().where(sign > 0), amt.abs().where(sign < 0)
            unknown = sign.isna() & amt.notna()
            notes.append("Ekstrede giriş/çıkış sütunu yoktu; yön bakiye değişiminden çıkarıldı.")
        else:
            inflow, outflow = amt.abs(), pd.Series(np.nan, index=df.index)
            notes.append("Ekstrede giriş/çıkış ayrımı (B/A sütunu, Borç/Alacak sütunları, eksi tutar ya da bakiye) "
                         "bulunamadı; bütün satırlar giriş sayıldı. Ekstrede çıkış hareketleri varsa tahsilatlar olduğundan "
                         "yüksek görünür: bankadan B/A sütunlu ya da işaretli tutarlı ekstre alın.")
    date, desc = _date(df["issue_date"]), df["description"].fillna("")

    def frame(values):
        out = pd.DataFrame({"date": date, "amount": values, "description": desc}).dropna(subset=["date", "amount"])
        return out[out["amount"] > 0].reset_index(drop=True)

    ins, outs = frame(inflow), frame(outflow)
    skipped = len(df) - len(ins) - len(outs)
    if unknown.any():
        notes.append(f"{int(unknown.sum())} satırın yönü bakiyeden çıkarılamadı ve atlandı.")
    elif skipped > 0:
        notes.append(f"Ekstrede {skipped} satır atlandı (okunamayan tarih/tutar).")
    if len(outs):
        notes.append(f"Ekstredeki {len(outs)} çıkış hareketi tahsilat sayılmadı; gider planının kontrolünde kullanılır.")
    if with_balance:
        return ins, outs, notes, (_last_balance(date, _num(df["balance"])) if "balance" in df else None)
    return ins, outs, notes


def load_payments(file, mapping: dict | None = None):
    """Banka ekstresi. Zorunlu: tarih, tutar, açıklama. Yalnızca hesaba girişler tahsilat olarak döner
    (bkz. bank_movements)."""
    ins, _, notes = bank_movements(file, mapping)
    return ins, notes


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


LEDGER_DEBIT = ["borc", "ana doviz borc", "borc tutari"]
LEDGER_CREDIT = ["alacak", "ana doviz alacak", "alacak tutari"]


def _ledger_columns(columns) -> tuple[str, str] | None:
    keys = {_key(c): c for c in columns}
    debit = next((keys[k] for k in LEDGER_DEBIT if k in keys), None)
    credit = next((keys[k] for k in LEDGER_CREDIT if k in keys), None)
    return (debit, credit) if debit is not None and credit is not None else None


def is_ledger(file) -> bool:
    """Borç ve alacak sütunları olan cari hesap ekstresi / muavin defter / cari hareket föyü mü?"""
    return _ledger_columns(_read(file).columns) is not None


def load_ledger(file, default_terms: int = 30, fallback_customer: str | None = None, with_events: bool = False):
    """Cari hesap hareketlerinden fatura listesi çıkarır.

    Borç satırları alacak doğurur (fatura, devir); alacak satırları onu kapatır (havale, çek, iade).
    Kapama, her müşteride en eski açık kalemden başlar (FIFO). Çek ya da senetle yapılan tahsilat
    cari hesabı kapatır ama para çekin vadesinde gelir; bu satırlar ayrıca çek listesi olarak döner.
    Dönen değer: (faturalar, notlar, çekler)."""
    notes: list[str] = []
    raw = _read(file)
    cols = _ledger_columns(raw.columns)
    if cols is None:
        raise ValueError("Borç ve alacak sütunları bulunamadı; bu dosya cari hesap ekstresi gibi görünmüyor.")
    debit, credit = _num(raw[cols[0]]).fillna(0), _num(raw[cols[1]]).fillna(0)
    df = _pick(raw.drop(columns=list(cols)), ["invoice_id", "customer_name", "vkn", "issue_date", "due_date",
                                             "description"], ["issue_date"])
    df["issue_date"] = _date(df["issue_date"])
    df["due_date"] = _date(df["due_date"]) if "due_date" in df else pd.NaT
    if "customer_name" not in df:
        if not fallback_customer:
            raise ValueError("Ekstrede müşteri (cari) sütunu yok; tek müşterili ekstrelerde müşteri adını belirtin.")
        df["customer_name"] = fallback_customer
        notes.append(f"Ekstrede müşteri sütunu yoktu; tüm hareketler '{fallback_customer}' carisine yazıldı.")
    df["customer_name"] = df["customer_name"].ffill()
    df["debit"], df["credit"] = debit.to_numpy(), credit.to_numpy()
    df["description"] = df["description"].fillna("") if "description" in df else ""
    df = df.dropna(subset=["issue_date"]).sort_values("issue_date", kind="stable").reset_index(drop=True)

    invoices, cheques, events, advance = [], [], [], 0.0
    for name, rows in df.groupby("customer_name", sort=False):
        queue = []                                     # bu müşterinin açık kalemleri, eskiden yeniye
        for r in rows.itertuples():
            if r.debit > 0:
                number = str(r.invoice_id).strip() if "invoice_id" in df and pd.notna(r.invoice_id) else ""
                item = {"invoice_id": number or f"CARI-{_key(name)[:20]}-{r.issue_date:%Y%m%d}-{r.Index}",
                        "customer_name": name, "vkn": getattr(r, "vkn", None), "issue_date": r.issue_date,
                        "due_date": r.due_date, "amount": r.debit, "open_amount": r.debit, "paid_date": pd.NaT,
                        "cheque_due": pd.NaT}
                invoices.append(item)
                queue.append(item)
            if r.credit > 0:
                remaining = r.credit
                text = _key(r.description)
                is_cheque = (bool(CHEQUE_WORDS.search(text)) and pd.notna(r.due_date)
                             and r.due_date > r.issue_date)
                while remaining > 0.005 and queue:
                    take = min(remaining, queue[0]["open_amount"])
                    queue[0]["open_amount"] -= take
                    remaining -= take
                    # Her dağıtım bir tahsilat olayıdır: taksitli ödemeler kendi tarihleriyle kalır.
                    events.append({"date": r.issue_date, "invoice_id": queue[0]["invoice_id"], "amount": take})
                    if queue[0]["open_amount"] <= 0.005:
                        queue[0]["open_amount"], queue[0]["paid_date"] = 0.0, r.issue_date
                        if is_cheque:
                            # Fatura çekle kapandı; para çek vadesinde gelir (pipeline.cheque_habits bunu öğrenir).
                            queue[0]["cheque_due"] = r.due_date
                        queue.pop(0)
                advance += remaining
                if is_cheque:
                    cheques.append({"date": r.due_date, "amount": r.credit, "label": name})
    if advance > 0.005:
        notes.append(f"Alacak satırlarından {advance:,.2f} TL karşılık gelen açık kalem bulunmadan kaldı (avans ya da "
                     "devir eksikliği); açık bakiyeyi kontrol edin.")
    out = pd.DataFrame(invoices)
    if out.empty:
        raise ValueError("Ekstrede borç (fatura) satırı bulunamadı.")
    cheque_frame = pd.DataFrame(cheques, columns=["date", "amount", "label"])
    if len(cheque_frame):
        notes.append(f"Ekstredeki {len(cheque_frame)} çek/senet tahsilatı ({cheque_frame['amount'].sum():,.0f} TL) "
                     "vadesinde kasaya girecek şekilde çek listesine eklendi.")
    finished = _finish_invoices(out, default_terms, notes)
    if with_events:
        ev = pd.DataFrame(events, columns=["date", "invoice_id", "amount"])
        return finished, notes, cheque_frame, ev[ev["invoice_id"].isin(finished["invoice_id"])].reset_index(drop=True)
    return finished, notes, cheque_frame


# Cari hesapta çek/senet tahsilatı açıklamaları (aksansız, küçük harf): "Çek tahsilatı", "Müşteri çeki",
# "Alınan çekler", "Senedi alındı", "Bono". "Çekim" gibi ilgisiz sözcükler eşleşmez.
CHEQUE_WORDS = re.compile(r"\b(cek|ceki|cekler|cekleri|cekle|senet|senedi|senetler|senetle|bono|bonosu)\b")
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
                     "ya da sonuçlanmış olduğu için tahmine katılmadı. Ciro edilen çek karşılıksız çıkarsa, aksi şart "
                     "edilmedikçe tedarikçiye karşı sorumluluğunuz sürer (TTK m.818 yollamasıyla m.685 ve 724).")
    return out[~gone].drop(columns="status").reset_index(drop=True), notes


# Tam günlük resmî tatiller (2429 sayılı Ulusal Bayram ve Genel Tatiller Hakkında Kanun; tarihler: Diyanet İşleri
# Başkanlığı, "2026 / 2027 Yılı Resmi Tatil Günleri", 20.10.2026'da okundu). Arife ve 28 Ekim öğleden sonra yarım gün
# tatildir; sabahı iş günü olduğu için ödeme o gün sayılır (erken saymak kasa açısından ihtiyatlı). Dini bayramlar
# her yıl güncellenir; 2028 ve sonrası için yalnızca sabit tarihli tatiller bilinir.
_FIXED_HOLIDAYS = ("01-01", "04-23", "05-01", "05-19", "07-15", "08-30", "10-29")
_RELIGIOUS_HOLIDAYS = {
    2026: ["2026-03-20", "2026-03-21", "2026-03-22", "2026-05-27", "2026-05-28", "2026-05-29", "2026-05-30"],
    2027: ["2027-03-09", "2027-03-10", "2027-03-11", "2027-05-16", "2027-05-17", "2027-05-18", "2027-05-19"],
}


def is_holiday(day) -> bool:
    day = pd.Timestamp(day)
    return f"{day:%m-%d}" in _FIXED_HOLIDAYS or f"{day:%Y-%m-%d}" in _RELIGIOUS_HOLIDAYS.get(day.year, [])


def next_business_day(day) -> pd.Timestamp:
    """VUK m.18/4: sürenin son günü resmî tatile rastlarsa süre, tatili izleyen ilk iş günü biter. Hafta sonu da
    tatil sayılır (vergi daireleri cumartesi ve pazar kapalı)."""
    day = pd.Timestamp(day)
    while day.dayofweek >= 5 or is_holiday(day):
        day += pd.Timedelta(days=1)
    return day


# Vergi takvimi (GİB): muhtasar ve prim hizmet beyannamesi ödemesi izleyen ayın 26'sı, KDV 28'i.
# SGK primi: izleyen ayın son günü. Son gün hafta sonuna ya da resmî tatile denk gelirse ilk iş gününe kayar.
# GİB'in süre uzatmaları önceden bilinmez; ödeme asıl son günde sayılır (kasa açısından ihtiyatlı).
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
                date = next_business_day(date)
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
