"""UBL-TR e-fatura ayrıştırıcı.

Vade tarihi UBL-TR'de her faturada bulunmayabilir; bu yüzden sırayla PaymentMeans,
PaymentTerms ve son olarak müşterinin varsayılan vadesi denenir ve hangisinin
kullanıldığı `due_source` alanında saklanır.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET

import pandas as pd

NS = {
    "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
    "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
}


def _text(node, path):
    el = node.find(path, NS)
    return el.text.strip() if el is not None and el.text else None


def parse_invoice(xml: str | bytes, default_terms_days: int | None = None) -> dict:
    root = ET.fromstring(xml)
    party = root.find("cac:AccountingCustomerParty/cac:Party", NS)
    vkn = None
    for el in party.findall("cac:PartyIdentification/cbc:ID", NS) if party is not None else []:
        if el.get("schemeID") in ("VKN", "TCKN") and el.text:
            vkn = el.text.strip()
            break
    issue = pd.Timestamp(_text(root, "cbc:IssueDate"))
    due, source = None, "missing"
    for path, name in (("cac:PaymentMeans/cbc:PaymentDueDate", "payment_means"),
                       ("cac:PaymentTerms/cbc:PaymentDueDate", "payment_terms")):
        value = _text(root, path)
        if value:
            due, source = pd.Timestamp(value), name
            break
    if due is None and default_terms_days is not None:
        due, source = issue + pd.Timedelta(days=default_terms_days), "default_terms"
    amount_el = root.find("cac:LegalMonetaryTotal/cbc:PayableAmount", NS)
    return {
        "invoice_id": _text(root, "cbc:ID"),
        "issue_date": issue,
        "due_date": due,
        "due_source": source,
        "vkn": vkn,
        "customer_name": _text(party, "cac:PartyName/cbc:Name") if party is not None else None,
        "amount": float(amount_el.text) if amount_el is not None else None,
        "currency": amount_el.get("currencyID") if amount_el is not None else None,
    }
