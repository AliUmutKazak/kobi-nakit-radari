"""Banka tahsilatlarını açık faturalarla eşleştirme.

Türkiye'de ödemeler çoğu zaman fatura bazında değil cari hesaba mahsuben gelir. Bu yüzden
önce birebir tutar eşleşmesi aranır, bulunamazsa ödeme müşterinin en eski açık
faturalarından başlayarak (FIFO) dağıtılır; kısmi ödeme desteklenir.
"""
from __future__ import annotations

import re

import pandas as pd


def _norm(s: str) -> str:
    table = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
    return re.sub(r"[^a-z0-9 ]", " ", str(s).translate(table).lower())


# GİB fatura numarası: 3 karakter seri + 4 haneli yıl + 9 haneli sıra (ör. GIB202600000142).
INVOICE_NO = re.compile(r"\b([A-Z0-9]{3}20\d{2}\d{9})\b")
TAX_ID = re.compile(r"(?:VKN|VERGI NO|V\.?K\.?N\.?)[\s:.]*(\d{10})\b|(?:TCKN|T\.?C\.?)[\s:.]*(\d{11})\b")
IBAN = re.compile(r"\bTR\d{24}\b")
# Banka önekleri ve şirket ekleri unvan karşılaştırmasından önce atılır.
_NOISE = {"gelen", "giden", "eft", "fast", "havale", "tt", "para", "transferi", "sorguno", "ref", "dekont", "odemesi",
          "odeme", "cari", "hesap", "hesabi", "hesaba", "mahsuben", "fatura", "faturasi", "nolu", "bedeli", "ltd", "sti",
          "tic", "san", "as", "ve", "pazarlama", "paz"}


def identify_customer(description: str, customers: pd.DataFrame) -> str | None:
    """Sırasıyla: açıklamadaki VKN/TCKN, açıklamada geçen VKN rakamları, unvanın ayırt edici kelimeleri."""
    upper = str(description).translate(str.maketrans("çğıöşüi", "ÇĞIÖŞÜİ")).upper()
    ids = {g for m in TAX_ID.finditer(upper.replace("İ", "I")) for g in m.groups() if g}
    by_vkn = {str(c.vkn): c.customer_id for c in customers.itertuples() if c.vkn}
    for tax_id in ids:
        if tax_id in by_vkn:
            return by_vkn[tax_id]
    text = _norm(description)
    for vkn, cid in by_vkn.items():
        if vkn in text:
            return cid
    best, best_score, runner_up = None, 0, 0
    words = set(text.split()) - _NOISE
    for c in customers.itertuples():
        tokens = {t for t in _norm(c.customer_name).split() if len(t) >= 2} - _NOISE
        score = len(tokens & words)
        if score > best_score:
            best, best_score, runner_up = c.customer_id, score, best_score
        elif score == best_score:
            runner_up = score
    # İki müşteri aynı puanı alıyorsa tahmin etmek yerine eşleşmeyen sayılır.
    return best if best_score >= 2 and best_score > runner_up else None


def sender_key(description: str) -> str:
    """Banka açıklamasından göndereni temsil eden anahtar: önekler, ekler ve sayılar atılmış kelimeler.

    Kullanıcı eşleşmeyen bir tahsilatı bir kez müşteriye bağladığında bu anahtar saklanır ve aynı
    gönderen sonraki ekstrelerde otomatik tanınır."""
    iban = IBAN.search(str(description).upper().replace(" ", ""))
    if iban:                         # IBAN, unvan yazımından bağımsız ve değişmeyen en sağlam anahtardır
        return "iban:" + iban.group(0)
    words = [w for w in _norm(description).split() if w not in _NOISE and not w.isdigit() and len(w) >= 2]
    return " ".join(dict.fromkeys(words))


def _alias_match(description: str, aliases: dict[str, str]) -> str | None:
    compact = str(description).upper().replace(" ", "")
    for key, cid in aliases.items():
        if key.startswith("iban:") and key[5:] in compact:
            return cid
    words = set(_norm(description).split())
    hits = [(len(k.split()), cid) for k, cid in aliases.items()
            if k and not k.startswith("iban:") and set(k.split()) <= words]
    return max(hits)[1] if hits else None


def reconcile(invoices: pd.DataFrame, payments: pd.DataFrame, tol: float = 0.01, aliases: dict[str, str] | None = None):
    """invoices: invoice_id, customer_id, customer_name, vkn, due_date, open_amount
    payments: date, amount, description
    aliases: kullanıcının daha önce müşteriye bağladığı gönderen anahtarları (sender_key -> customer_id)
    Döner: (güncellenmiş faturalar, eşleşme satırları, eşleşmeyen ödemeler)."""
    known = set(invoices["customer_id"])
    aliases = {k: v for k, v in (aliases or {}).items() if v in known}
    inv = invoices.copy().reset_index(drop=True)
    inv["open_amount"] = inv["open_amount"].astype(float)
    if "paid_date" not in inv:
        inv["paid_date"] = pd.NaT
    customers = inv.drop_duplicates("customer_id")[["customer_id", "customer_name", "vkn"]]
    allocations, unmatched = [], []
    by_number = {str(v).upper(): i for i, v in inv["invoice_id"].items()}
    for p in payments.sort_values("date").itertuples():
        # Açıklamada fatura numarası geçiyorsa müşteri ve fatura doğrudan bellidir.
        named = [by_number[n] for n in INVOICE_NO.findall(str(p.description).upper()) if n in by_number]
        cid = (inv.at[named[0], "customer_id"] if named
               else _alias_match(p.description, aliases) or identify_customer(p.description, customers))
        if cid is None:
            unmatched.append(p._asdict())
            continue
        cand = inv[(inv["customer_id"] == cid) & (inv["open_amount"] > tol)].sort_values("due_date")
        exact = cand[(cand["open_amount"] - p.amount).abs() <= tol]
        first = [i for i in named if inv.at[i, "open_amount"] > tol]
        order = first + [i for i in (exact.index[:1] if len(exact) else cand.index) if i not in first]
        method = "fatura_no" if first else ("exact" if len(exact) else "fifo")
        remaining = float(p.amount)
        for idx in order:
            if remaining <= tol:
                break
            take = min(remaining, inv.at[idx, "open_amount"])
            inv.at[idx, "open_amount"] -= take
            remaining -= take
            if inv.at[idx, "open_amount"] <= tol:
                inv.at[idx, "open_amount"] = 0.0
                inv.at[idx, "paid_date"] = p.date
            allocations.append({"date": p.date, "invoice_id": inv.at[idx, "invoice_id"], "amount": take,
                                "method": method})
        if remaining > tol:  # müşteri avansı / fazla ödeme
            unmatched.append({**p._asdict(), "amount": remaining, "customer_id": cid})
    return inv, pd.DataFrame(allocations), pd.DataFrame(unmatched)
