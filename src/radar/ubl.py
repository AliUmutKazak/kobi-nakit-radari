"""UBL-TR e-fatura ayrıştırıcı.

Vade tarihi UBL-TR'de her faturada bulunmayabilir; bu yüzden sırayla PaymentMeans,
PaymentTerms ve son olarak müşterinin varsayılan vadesi denenir ve hangisinin
kullanıldığı `due_source` alanında saklanır.
"""
from __future__ import annotations

# Dışarıdan gelen XML için güvenli ayrıştırıcı: varlık genişletme ("billion laughs") ve dış
# varlık saldırılarını reddeder.
from defusedxml import ElementTree as ET

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
        "invoice_type": _text(root, "cbc:InvoiceTypeCode"),
        "scenario": (_text(root, "cbc:ProfileID") or "").upper() or None,     # TEMELFATURA, TICARIFATURA ...
        "issue_date": issue,
        "due_date": due,
        "due_source": source,
        "vkn": vkn,
        "customer_name": _text(party, "cac:PartyName/cbc:Name") if party is not None else None,
        "amount": float(amount_el.text) if amount_el is not None else None,
        "currency": amount_el.get("currencyID") if amount_el is not None else None,
    }


# Uygulama yanıtı (GİB, "UBL-TR Uygulama Yanıtı" kılavuzu v0.2 ve "UBL-TR Ticari Fatura Senaryosu" v0.3, UBL-TR 1.2.1
# paketi): ticari fatura senaryosunda alıcı faturayı KABUL, RED ya da IADE yanıtıyla cevaplar. Yanıt
# cac:DocumentResponse altında cac:Response/cbc:ResponseCode ve yanıtlanan faturanın numarası
# cac:DocumentReference/cbc:ID olarak yer alır. RED: fatura "eksik, yanlış, hatalı veya satış anlaşması ile ilgili
# nedenlerden dolayı" reddedilmiştir. Yanıtın açıklama metni (red nedeni) okunmaz ve saklanmaz (KVKK m.4/2-ç).
RESPONSE_CODES = ("KABUL", "RED", "IADE")


def document_kind(xml: str | bytes) -> str | None:
    """'invoice', 'response' ya da tanınmayan belge için None."""
    tag = ET.fromstring(xml).tag
    name = tag.rsplit("}", 1)[-1]
    return {"Invoice": "invoice", "ApplicationResponse": "response"}.get(name)


def parse_application_response(xml: str | bytes) -> list[dict]:
    """Uygulama yanıtındaki her belge yanıtı: yanıtlanan fatura numarası, yanıt kodu, yanıt tarihi."""
    root = ET.fromstring(xml)
    issued = _text(root, "cbc:IssueDate")
    out = []
    for doc in root.findall("cac:DocumentResponse", NS):
        code = (_text(doc, "cac:Response/cbc:ResponseCode") or "").upper()
        ref = _text(doc, "cac:DocumentReference/cbc:ID")
        if ref and code in RESPONSE_CODES:
            out.append({"invoice_id": ref, "response": code, "response_date": pd.Timestamp(issued) if issued else pd.NaT})
    return out
