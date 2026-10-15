"""Pilot için veri anonimleştirme (takma adlandırma).

Mali müşavir ya da işletme, dosyaları paylaşmadan önce kendi bilgisayarında çalıştırır:

- Müşteri unvanı ve VKN/TCKN, gizli bir anahtarla üretilen sabit takma adlarla değiştirilir
  (HMAC-SHA256). Aynı müşteri her dosyada ve her ay aynı takma adı alır; anahtar olmadan takma
  addan gerçek kişiye/şirkete dönülemez. Anahtar yalnızca veriyi hazırlayanın bilgisayarında kalır.
- E-posta ve telefon atılır.
- Banka açıklamaları hiçbir zaman olduğu gibi aktarılmaz: serbest metinde geçen kişi adlarını
  güvenle bulmak mümkün olmadığından açıklama tümüyle silinir; yerine yalnızca eşleşen müşterinin
  takma adı, takma VKN'si ve açıklamada geçen GİB fatura numarası yazılır. Eşleşmeyen satırda
  yalnızca "eşleşmedi" kalır.
- Fatura numaraları da takma numaralarla değişir: GİB biçimindeki numaranın ilk üç harfi işletmeye
  özgü seridir; cari ekstreden okunan numarasız satırlarda ise kimlik müşteri adından üretilir.
  Takma numara GİB biçimindedir (ANO + yıl + 9 hane), böylece banka eşleştirmesi anonim veride de çalışır.
- Tutar ve tarihler korunur: tahminin dayandığı bilgi bunlardır.

Sınır: Tutar ve tarih örüntüleri, dış bilgiyle birleştirildiğinde bir işletmeyi tanınabilir kılabilir.
KVKK açısından bu yöntem "takma adlandırma"dır; tam anonimlik iddia edilmez. Müşterilerin çoğu tüzel
kişi olduğu için (unvan ve VKN kişisel veri değildir) risk sınırlıdır; şahıs işletmeleri için
paylaşım öncesi hukuki değerlendirme gerekir.
"""
from __future__ import annotations

import hashlib
import hmac
import io
import os
import secrets
import zipfile
from pathlib import Path

import pandas as pd

from .reconcile import INVOICE_NO, identify_customer


def key_path() -> Path:
    base = os.environ.get("LOCALAPPDATA") or Path.home() / ".local" / "share"
    return Path(base) / "KobiRadar" / "anonim_anahtar.txt"


def load_or_create_key(path: Path | None = None) -> str:
    """Anahtar bir kez üretilir ve bu bilgisayarda saklanır; aynı anahtar her ay aynı takma adları verir."""
    path = path or key_path()
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    path.parent.mkdir(parents=True, exist_ok=True)
    key = secrets.token_hex(32)
    path.write_text(key, encoding="utf-8")
    return key


def _digest(key: str, value: str) -> str:
    return hmac.new(key.encode(), str(value).strip().upper().encode("utf-8"), hashlib.sha256).hexdigest()


def pseudonym(key: str, customer_id: str) -> tuple[str, str]:
    """(takma unvan, takma 10 haneli VKN). Aynı anahtar ve müşteri için her zaman aynı."""
    h = _digest(key, customer_id)
    return f"Müşteri {h[:6].upper()}", str(int(h[6:22], 16) % 9_000_000_000 + 1_000_000_000)


def firm_alias(key: str, company: str) -> str:
    """İşletmenin takma adı; aynı anahtar ve unvan için her ay aynı."""
    return f"Isletme_{_digest(key, company)[:6].upper()}"


def invoice_aliases(inv: pd.DataFrame, key: str) -> dict[str, str]:
    """Gerçek fatura no → takma fatura no (ANO + fatura yılı + 9 hane). Aynı anahtarla her ay aynı."""
    out = {}
    for number, issued in zip(inv["invoice_id"].astype(str), inv["issue_date"]):
        year = f"{issued:%Y}" if pd.notna(issued) and 2000 <= issued.year <= 2099 else "2000"
        out[number] = f"ANO{year}{int(_digest(key, 'fatura:' + number)[:15], 16) % 1_000_000_000:09d}"
    if len(set(out.values())) < len(out):
        raise ValueError("Takma fatura numaralarında çakışma oldu; anahtarı yenileyip tekrar deneyin.")
    return out


def anonymize_invoices(inv: pd.DataFrame, key: str) -> pd.DataFrame:
    """Standart fatura tablosundaki kimlik bilgilerini ve fatura numaralarını takma adlarla değiştirir."""
    out = inv.copy()
    out["invoice_id"] = out["invoice_id"].astype(str).map(invoice_aliases(inv, key))
    names = {cid: pseudonym(key, cid) for cid in out["customer_id"].unique()}
    out["customer_name"] = out["customer_id"].map(lambda c: names[c][0])
    out["vkn"] = out["customer_id"].map(lambda c: names[c][1])
    out["customer_id"] = out["vkn"]
    for col in ("email", "phone"):
        if col in out:
            out[col] = ""
    return out


def anonymize_payments(payments: pd.DataFrame, raw_invoices: pd.DataFrame, key: str,
                       aliases: dict[str, str] | None = None) -> pd.DataFrame:
    """Banka tahsilatlarının açıklamasını, gerçek veriyle eşleştirdikten sonra tümüyle yeniden yazar."""
    customers = raw_invoices.drop_duplicates("customer_id")[["customer_id", "customer_name", "vkn"]]
    known_numbers = set(raw_invoices["invoice_id"].astype(str).str.upper())
    numbers_alias = {k.upper(): v for k, v in invoice_aliases(raw_invoices, key).items()}
    from .reconcile import _alias_match
    rows = []
    for p in payments.itertuples():
        numbers = [n for n in INVOICE_NO.findall(str(p.description).upper()) if n in known_numbers]
        cid = None
        if numbers:
            cid = raw_invoices.loc[raw_invoices["invoice_id"].astype(str).str.upper() == numbers[0], "customer_id"].iloc[0]
        cid = cid or (_alias_match(p.description, aliases) if aliases else None) or identify_customer(p.description, customers)
        if cid is None:
            text = "GELEN | eşleşmedi"
        else:
            name, vkn = pseudonym(key, cid)
            text = f"GELEN | {name} | VKN:{vkn}" + (f" | {numbers_alias[numbers[0]]}" if numbers else "")
        rows.append({"date": p.date, "amount": p.amount, "description": text})
    return pd.DataFrame(rows, columns=["date", "amount", "description"])


def to_csv_bytes(df: pd.DataFrame, columns: dict[str, str]) -> bytes:
    """Panelin doğrudan okuyabileceği Türkçe başlıklı CSV."""
    frame = df[list(columns)].rename(columns=columns)
    return frame.to_csv(sep=";", decimal=",", index=False, date_format="%d.%m.%Y").encode("utf-8-sig")


INVOICE_COLUMNS = {"invoice_id": "Fatura No", "customer_name": "Cari Unvan", "vkn": "VKN", "issue_date": "Fatura Tarihi",
                   "due_date": "Vade Tarihi", "amount": "Tutar", "open_amount": "Kalan", "paid_date": "Ödeme Tarihi"}
PAYMENT_COLUMNS = {"date": "Tarih", "amount": "Tutar", "description": "Açıklama"}


SAFE_LABELS = ("maaş", "kira", "sgk", "kdv", "muhtasar", "vergi", "kredi", "elektrik", "doğalgaz", "su",
               "ödenecek faturalar", "tedarikçi ödemeleri", "sigorta", "aidat")


def _safe_label(value) -> str:
    """Gider kalemlerinden yalnızca genel kategori adları kalır; serbest metin (kişi ya da firma adı
    içerebilir) "Diğer" olur."""
    text = str(value).strip().lower()
    return next((lab.capitalize() for lab in SAFE_LABELS if lab in text), "Diğer" if text else "")


def package(company: str, invoices: pd.DataFrame, key: str, payments: pd.DataFrame | None = None,
            extra: dict[str, pd.DataFrame] | None = None) -> tuple[bytes, dict]:
    """Bir işletmenin anonimleştirilmiş dosyalarını zip olarak verir; yanında ne yapıldığının özeti.

    `invoices` ve `payments` henüz anonimleştirilmemiş standart tablolardır; `extra` (giderler, çekler)
    yalnızca tarih ve tutar içerir, açıklamaları atılır."""
    firm = firm_alias(key, company)
    anon_inv = anonymize_invoices(invoices, key)
    summary = {"işletme_takma_adı": firm, "fatura": len(anon_inv), "müşteri": int(anon_inv["customer_id"].nunique()),
               "dönem": f"{invoices['issue_date'].min():%d.%m.%Y} – {invoices['issue_date'].max():%d.%m.%Y}",
               "silinen_alanlar": "unvan ve VKN takma adla değişti; e-posta ve telefon silindi"}
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(f"{firm}/faturalar.csv", to_csv_bytes(anon_inv, INVOICE_COLUMNS))
        if payments is not None and len(payments):
            anon_pay = anonymize_payments(payments, invoices, key)
            z.writestr(f"{firm}/ekstre.csv", to_csv_bytes(anon_pay, PAYMENT_COLUMNS))
            summary["banka_satırı"] = len(anon_pay)
            summary["eşleşmeyen_banka_satırı"] = int((anon_pay["description"] == "GELEN | eşleşmedi").sum())
            summary["silinen_alanlar"] += "; banka açıklamaları tümüyle yeniden yazıldı"
        for name, frame in (extra or {}).items():
            if frame is not None and len(frame):
                cols = {c: c for c in ("date", "amount", "label") if c in frame}
                safe = frame[list(cols)].copy()
                if "label" in safe:
                    safe["label"] = safe["label"].map(_safe_label)
                z.writestr(f"{firm}/{name}.csv",
                           to_csv_bytes(safe, {"date": "Vade", "amount": "Tutar", "label": "Kalem"} if "label" in safe
                                        else {"date": "Vade", "amount": "Tutar"}))
        z.writestr(f"{firm}/BENİ_OKU.txt", ("Bu klasör KOBİ Nakit Akışı Radarı pilotu için anonimleştirildi.\r\n"
                                            + "\r\n".join(f"{k}: {v}" for k, v in summary.items())).encode("utf-8-sig"))
    return buf.getvalue(), summary
