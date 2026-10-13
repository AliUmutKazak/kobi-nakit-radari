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


def identify_customer(description: str, customers: pd.DataFrame) -> str | None:
    """Açıklamada VKN geçiyorsa onu, yoksa unvanın ayırt edici kelimelerini kullanır."""
    text = _norm(description)
    for c in customers.itertuples():
        if c.vkn and str(c.vkn) in text:
            return c.customer_id
    best, best_score = None, 0
    words = set(text.split())
    for c in customers.itertuples():
        tokens = {t for t in _norm(c.customer_name).split() if len(t) >= 2 and t not in {"ltd", "sti", "tic", "san", "as", "ve"}}
        score = len(tokens & words)
        if score > best_score:
            best, best_score = c.customer_id, score
    return best if best_score >= 2 else None


def reconcile(invoices: pd.DataFrame, payments: pd.DataFrame, tol: float = 0.01):
    """invoices: invoice_id, customer_id, customer_name, vkn, due_date, open_amount
    payments: date, amount, description
    Döner: (güncellenmiş faturalar, eşleşme satırları, eşleşmeyen ödemeler)."""
    inv = invoices.copy().reset_index(drop=True)
    inv["open_amount"] = inv["open_amount"].astype(float)
    if "paid_date" not in inv:
        inv["paid_date"] = pd.NaT
    customers = inv.drop_duplicates("customer_id")[["customer_id", "customer_name", "vkn"]]
    allocations, unmatched = [], []
    for p in payments.sort_values("date").itertuples():
        cid = identify_customer(p.description, customers)
        if cid is None:
            unmatched.append(p._asdict())
            continue
        cand = inv[(inv["customer_id"] == cid) & (inv["open_amount"] > tol)].sort_values("due_date")
        exact = cand[(cand["open_amount"] - p.amount).abs() <= tol]
        remaining = float(p.amount)
        for idx in (exact.index[:1] if len(exact) else cand.index):
            if remaining <= tol:
                break
            take = min(remaining, inv.at[idx, "open_amount"])
            inv.at[idx, "open_amount"] -= take
            remaining -= take
            if inv.at[idx, "open_amount"] <= tol:
                inv.at[idx, "open_amount"] = 0.0
                inv.at[idx, "paid_date"] = p.date
            allocations.append({"date": p.date, "invoice_id": inv.at[idx, "invoice_id"], "amount": take,
                                "method": "exact" if len(exact) else "fifo"})
        if remaining > tol:  # müşteri avansı / fazla ödeme
            unmatched.append({**p._asdict(), "amount": remaining, "customer_id": cid})
    return inv, pd.DataFrame(allocations), pd.DataFrame(unmatched)
