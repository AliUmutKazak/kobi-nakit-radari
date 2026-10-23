"""Dosya alma: fatura listesi, cari ekstre, banka ekstresi, UBL-TR e-fatura."""

import pandas as pd
import pytest

from radar.reconcile import reconcile
from radar.synthetic import generate, observe, to_ubl_xml
from radar.ubl import parse_invoice

from conftest import AS_OF


def test_ubl_roundtrip_and_missing_due_date(full):
    row = full.iloc[0]
    parsed = parse_invoice(to_ubl_xml(row))
    assert parsed["invoice_id"] == row["invoice_id"] and parsed["vkn"] == row["vkn"]
    assert parsed["due_date"] == row["due_date"].normalize() and parsed["due_source"] == "payment_means"
    assert parsed["amount"] == pytest.approx(row["amount"])

    no_due = parse_invoice(to_ubl_xml(row, with_due_date=False))
    assert no_due["due_date"] is None and no_due["due_source"] == "missing"
    fallback = parse_invoice(to_ubl_xml(row, with_due_date=False), default_terms_days=45)
    assert fallback["due_date"] == row["issue_date"].normalize() + pd.Timedelta(days=45)


def test_ingest_reports_missing_columns_and_defaults(tmp_path):
    from radar import ingest

    p = tmp_path / "f.csv"
    p.write_text("Fatura No;Cari;Tarih;Toplam\nA1;Deneme Ltd;05.09.2026;1.250,50\nA2;Deneme Ltd;;100\n", encoding="utf-8")
    inv, notes = ingest.load_invoices(p, default_terms=45)
    assert len(inv) == 1 and inv.at[0, "amount"] == 1250.50
    assert inv.at[0, "due_date"] == pd.Timestamp("2026-10-20") and len(notes) == 2
    p.write_text("Belge;Kime\nA1;X\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Eksik sütun"):
        ingest.load_invoices(p)


def test_manual_column_mapping(tmp_path):
    from radar import ingest

    p = tmp_path / "f.csv"
    p.write_text("Evrak;Kime Kesildi;Kesim Günü;Net\nA1;Deneme Ltd;05.09.2026;1.250,50\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Eksik sütun"):
        ingest.load_invoices(p)
    assert ingest.columns(p) == ["Evrak", "Kime Kesildi", "Kesim Günü", "Net"]
    mapping = {"invoice_id": "Evrak", "customer_name": "Kime Kesildi", "issue_date": "Kesim Günü", "amount": "Net"}
    inv, _ = ingest.load_invoices(p, mapping=mapping)
    assert inv.at[0, "invoice_id"] == "A1" and inv.at[0, "amount"] == 1250.50


def test_foreign_currency_and_refund_invoices_are_reported_not_mixed(tmp_path, full):
    from radar import ingest

    p = tmp_path / "f.csv"
    p.write_text("Fatura No;Cari;Tarih;Toplam;Para Birimi;Fatura Tipi\n"
                 "A1;Deneme Ltd;05.09.2026;1000;TL;SATIS\n"
                 "A2;Deneme Ltd;06.09.2026;500;USD;SATIS\n"
                 "A3;Deneme Ltd;07.09.2026;200;TRY;IADE\n"
                 "A4;Deneme Ltd;08.09.2026;300;;SATIS\n", encoding="utf-8")
    inv, notes = ingest.load_invoices(p)
    assert list(inv["invoice_id"]) == ["A1", "A4"] and inv["amount"].sum() == 1300
    assert any("USD" in n for n in notes) and any("iade" in n for n in notes)

    row = full.iloc[0]
    usd = to_ubl_xml(row).replace('currencyID="TRY"', 'currencyID="USD"')
    refund = to_ubl_xml(row).replace("<cbc:IssueDate>", "<cbc:InvoiceTypeCode>IADE</cbc:InvoiceTypeCode><cbc:IssueDate>")
    df, notes = ingest.load_ubl([usd.encode(), refund.encode()])
    assert df.empty and len(notes) == 2
    ok, notes = ingest.load_ubl([to_ubl_xml(row).encode()])
    assert len(ok) == 1 and not notes


def test_refunds_are_netted_and_currency_converted_with_given_rates(tmp_path):
    from radar import ingest

    p = tmp_path / "f.csv"
    p.write_text("Fatura No;Cari;Tarih;Vade;Toplam;Para Birimi;Fatura Tipi\n"
                 "A1;Deneme Ltd;01.08.2026;01.09.2026;1000;TL;SATIS\n"
                 "A2;Deneme Ltd;05.08.2026;05.09.2026;500;TL;SATIS\n"
                 "R1;Deneme Ltd;10.09.2026;;1200;TL;IADE\n"
                 "B1;Baska AS;02.08.2026;02.09.2026;100;USD;SATIS\n"
                 "B2;Baska AS;03.08.2026;03.09.2026;10;EUR;SATIS\n", encoding="utf-8")
    inv, notes = ingest.load_invoices(p, rates=ingest.parse_rates("usd = 40,5; GBP=yok"))
    by = inv.set_index("invoice_id")
    assert list(by.index) == ["A1", "B1", "A2"]                       # EUR kuru yok: dışarıda; iade satır değil
    assert by.at["A1", "open_amount"] == 0 and by.at["A2", "open_amount"] == 300      # 1200 TL iade, eskiden yeniye
    assert by.at["B1", "amount"] == pytest.approx(4050) and by.at["B1", "currency"] == "USD"
    assert sum("EUR" in n for n in notes) == 1 and any("USD = 40.5" in n for n in notes) and any("iade" in n for n in notes)
    assert ingest.parse_rates("") == {} and ingest.parse_rates("EUR=48,2\nusd=41") == {"EUR": 48.2, "USD": 41.0}


def test_bank_statement_with_preamble_direction_and_rich_descriptions(tmp_path):
    from radar import ingest

    p = tmp_path / "ziraat.csv"
    p.write_text(
        "Hesap No;12345678\nIBAN;TR000000000000000000000000\nDönem;01.10.2026 - 31.10.2026\n\n"
        "İşlem Tarihi;Açıklama;İşlem Tutarı (TL);B/A;Bakiye (TL)\n"
        "05.10.2026;GELEN EFT - ÖRNEK LOJİSTİK A.Ş. - VKN:6480591234 - GIB2026000000142 NOLU FATURA;144.000,00;A;412.500,00\n"
        "07.10.2026;FAST GELEN - KUZEY YILDIZI MAKİNA SAN. LTD. ŞTİ. - SORGUNO:0482910;60.000,00;A;472.500,00\n"
        "09.10.2026;GİDEN EFT - MARMARA ENERJİ - EKİM;18.450,00;B;454.050,00\n"
        "10.10.2026;ÜYE İŞYERİ POS BLOKE ÇÖZÜMÜ;24.375,00;A;478.425,00\n", encoding="utf-8")
    pay, notes = ingest.load_payments(p)
    assert len(pay) == 3 and pay["amount"].sum() == 144000 + 60000 + 24375      # giden EFT düştü

    inv = pd.DataFrame({
        "invoice_id": ["GIB2026000000141", "GIB2026000000142", "K1", "K2"],
        "customer_id": ["6480591234", "6480591234", "K", "K"],
        "customer_name": ["Örnek Lojistik ve Depolama A.Ş.", "Örnek Lojistik ve Depolama A.Ş.",
                          "Kuzey Yıldızı Makina San. Ltd. Şti.", "Kuzey Yıldızı Makina San. Ltd. Şti."],
        "vkn": ["6480591234", "6480591234", "", ""],
        "due_date": pd.to_datetime(["2026-09-01", "2026-10-01", "2026-09-05", "2026-09-20"]),
        "open_amount": [50000.0, 144000.0, 40000.0, 40000.0]})
    out, alloc, unmatched = reconcile(inv, pay)
    by = out.set_index("invoice_id")["open_amount"]
    # Fatura numarası açıklamada geçtiği için daha eski fatura değil, adı geçen fatura kapandı.
    assert by["GIB2026000000142"] == 0 and by["GIB2026000000141"] == 50000
    assert by["K1"] == 0 and by["K2"] == 20000                                  # unvanla bulundu, FIFO
    assert list(alloc["method"])[:1] == ["fatura_no"] and len(unmatched) == 1   # POS satırı müşteriye bağlanmadı


def test_mikro_series_number_phone_and_cheque_status(tmp_path):
    from radar import ingest

    p = tmp_path / "mikro.csv"
    p.write_text("Evrak Tarihi;Evrak Seri;Evrak Sıra;Cari İsmi;Vade Tarihi;Genel Toplam;Telefon\n"
                 "02.10.2026;MKR;2026000418;Ege Plastik Kalıp A.Ş.;01.12.2026;318.000,00;0532 123 45 67\n",
                 encoding="utf-8")
    inv, _ = ingest.load_invoices(p)
    assert inv.at[0, "invoice_id"] == "MKR2026000418" and inv.at[0, "phone"] == "905321234567"
    assert ingest.normalize_phone("5321234567") == "905321234567" and ingest.normalize_phone("0212 555 11 22") == ""

    c = tmp_path / "cek.csv"
    c.write_text("Vade;Tutar;Keşideci;Durum\n15.12.2026;200.000;Ege Plastik;Portföyde\n"
                 "20.12.2026;100.000;Bursa Oto;Tedarikçiye ciro edildi\n10.01.2027;50.000;Delta;Bankaya tahsile verildi\n"
                 "12.01.2027;70.000;Delta;Faktoringe iskonto\n", encoding="utf-8")
    chq, notes = ingest.load_cheques(c)
    assert list(chq["amount"]) == [200000, 50000] and "170,000" in notes[0]


def test_ledger_import_mikro_style_with_cheque(tmp_path):
    from radar import ingest

    p = tmp_path / "mikro_foy.csv"
    p.write_text(
        "Evrak Tarihi;Evrak No;Evrak Tipi;Cari Kodu;Cari İsmi;Vade Tarihi;Açıklama;Borç;Alacak;Bakiye\n"
        "02.08.2026;MKR001;Satış Faturası;120.01;Ege Plastik A.Ş.;01.09.2026;Fatura;318.000,00;0;318.000,00\n"
        "15.08.2026;MKR002;Satış Faturası;120.01;Ege Plastik A.Ş.;14.09.2026;Fatura;100.000,00;0;418.000,00\n"
        "06.09.2026;CEK082;Çek Giriş Bordrosu;120.01;Ege Plastik A.Ş.;15.12.2026;Çek tahsilatı;0;200.000,00;218.000,00\n"
        "10.09.2026;EFT1;Havale;120.01;Ege Plastik A.Ş.;;Gelen EFT;0;150.000,00;68.000,00\n"
        "11.09.2026;MKR003;Satış Faturası;120.02;Bursa Oto Ltd.;;Fatura;50.000,00;0;50.000,00\n",
        encoding="utf-8")
    assert ingest.is_ledger(p)
    inv, notes, chq = ingest.load_ledger(p, default_terms=30)
    by = inv.set_index("invoice_id")
    # 200.000 çek + 150.000 havale en eski faturadan başlayarak kapatır: MKR001 kapanır, MKR002'de 68.000 kalır.
    assert by.at["MKR001", "open_amount"] == 0 and by.at["MKR001", "paid_date"] == pd.Timestamp("2026-09-10")
    assert by.at["MKR002", "open_amount"] == 68000 and by.at["MKR003", "open_amount"] == 50000
    assert by.at["MKR003", "due_date"] == pd.Timestamp("2026-10-11")              # vade yok: +30 gün
    assert list(chq["amount"]) == [200000] and chq.at[0, "date"] == pd.Timestamp("2026-12-15")
    assert any("çek" in n for n in notes)
    assert "cheque_due" not in inv          # son kapatan havale: para o gün gelmiş sayılır
    # Her alacak dağıtımı bir tahsilat olayıdır: MKR001 çek (200.000) ve havaleyle (118.000) iki taksitte kapandı.
    _, _, _, ev = ingest.load_ledger(p, default_terms=30, with_events=True)
    first = ev[ev["invoice_id"] == "MKR001"].sort_values("date")
    assert list(first["amount"]) == [200000, 118000] and ev.loc[ev["invoice_id"] == "MKR002", "amount"].sum() == 32000

    q = tmp_path / "cek_kapatir.csv"
    q.write_text(
        "Evrak Tarihi;Evrak No;Cari İsmi;Vade Tarihi;Açıklama;Borç;Alacak\n"
        "02.08.2026;F1;Ege Plastik A.Ş.;01.09.2026;Fatura;100.000,00;0\n"
        "06.09.2026;C1;Ege Plastik A.Ş.;15.12.2026;Müşteri çeki;0;100.000,00\n", encoding="utf-8")
    inv2, _, _ = ingest.load_ledger(q)
    assert inv2.set_index("invoice_id").at["F1", "cheque_due"] == pd.Timestamp("2026-12-15")


def test_ledger_single_customer_bizimhesap_style(tmp_path):
    from radar import ingest

    p = tmp_path / "Delta Elektrik.csv"
    p.write_text("Tarih;Belge Numarası;Vade Tarihi;Açıklama (İşlem Türü);Borç (TL);Alacak (TL);Bakiye (TL);B/A\n"
                 "01.10.2026;BZH512;31.10.2026;Mal Satış Faturası;96.000,00;0,00;96.000,00;B\n"
                 "09.10.2026;EFT-948;09.10.2026;Banka Havale Tahsilatı;0,00;146.000,00;-50.000,00;A\n", encoding="utf-8")
    with pytest.raises(ValueError, match="müşteri"):
        ingest.load_ledger(p)
    inv, notes, chq = ingest.load_ledger(p, fallback_customer="Delta Elektrik")
    assert inv.at[0, "open_amount"] == 0 and inv.at[0, "customer_name"] == "Delta Elektrik" and chq.empty
    assert any("50,000.00" in n for n in notes)                                    # fazla ödeme bildirildi


def test_sample_ledger_reproduces_open_receivables(tmp_path):
    from radar import ingest
    from radar.synthetic import export_samples

    export_samples(tmp_path, seed=3, as_of=AS_OF)
    inv, notes, chq = ingest.load_ledger(tmp_path / "cari_ekstre.csv")
    truth = observe(generate(seed=3, as_of=AS_OF), AS_OF)
    assert len(inv) == len(truth) and inv["open_amount"].sum() == pytest.approx(truth["open_amount"].sum(), rel=1e-6)


def test_excel_damage_repairs_and_luca_account_names(tmp_path):
    from radar import ingest

    p = tmp_path / "luca.csv"
    p.write_text("Evrak Tarihi;Evrak No;Hesap Adı;VKN;Tutar;Döviz\n"
                 "03.10.2026;E1;120.01.0012 Trakya Tarım Ürünleri Paz. Ltd. Şti.;540123987;108.000,00;TRL\n"
                 "04.10.2026;E2;120.01.0034 - Başkent Medikal A.Ş.;1920384756.0;72.000,00;TL\n", encoding="utf-8")
    inv, notes = ingest.load_invoices(p)
    assert list(inv["vkn"]) == ["0540123987", "1920384756"] and not any("atlandı" in n for n in notes)
    assert list(inv["customer_name"]) == ["Trakya Tarım Ürünleri Paz. Ltd. Şti.", "Başkent Medikal A.Ş."]


def test_possible_duplicate_invoices_are_flagged_not_removed():
    from radar import ingest
    df = pd.DataFrame({"invoice_id": ["A1", "GIB2026000000001", "A2", "A3"], "customer_id": ["C1", "C1", "C1", "C2"],
                       "customer_name": ["Ege A.Ş."] * 3 + ["Bursa Ltd."],
                       "issue_date": pd.to_datetime(["2026-09-01", "2026-09-01", "2026-09-02", "2026-09-01"]),
                       "amount": [1000.0, 1000.0, 1000.0, 1000.0]})
    dup = ingest.possible_duplicates(df)
    assert len(dup) == 1 and dup.iloc[0]["invoice_ids"] == "A1, GIB2026000000001" and dup.iloc[0]["n"] == 2


def test_currency_spellings_from_accounting_exports():
    from radar import ingest
    df = pd.DataFrame({"currency": ["$", "Dolar", "€", "Avro", "EURO", "£", "Sterlin", "TL", "₺", None, " usd "]})
    assert ingest._currency_codes(df).tolist() == ["USD", "USD", "EUR", "EUR", "EUR", "GBP", "GBP", "TRY", "TRY", "TRY",
                                                   "USD"]


APP_RESPONSE = """<?xml version="1.0" encoding="UTF-8"?>
<ApplicationResponse xmlns="urn:oasis:names:specification:ubl:schema:xsd:ApplicationResponse-2"
  xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
  xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
  <cbc:ProfileID>TICARIFATURA</cbc:ProfileID><cbc:ID>YNT2026000000001</cbc:ID><cbc:IssueDate>{date}</cbc:IssueDate>
  <cbc:Note>Fiyat sözleşmeye aykırı</cbc:Note>
  <cac:DocumentResponse>
    <cac:Response><cbc:ReferenceID>1</cbc:ReferenceID><cbc:ResponseCode>{code}</cbc:ResponseCode></cac:Response>
    <cac:DocumentReference><cbc:ID>{invoice}</cbc:ID><cbc:DocumentTypeCode>FATURA</cbc:DocumentTypeCode></cac:DocumentReference>
  </cac:DocumentResponse>
</ApplicationResponse>"""


def test_efatura_application_response_marks_rejected_invoices_disputed(full):
    """GİB UBL-TR Ticari Fatura Senaryosu: alıcı faturayı KABUL, RED ya da IADE yanıtıyla cevaplar. RED alan fatura
    itirazlı sayılır ve tahmine girmez; red nedeni metni saklanmaz."""
    from radar import ingest, ubl
    obs = observe(full, AS_OF)
    rows = obs[obs["open_amount"] > 0].head(3)
    invoices = [to_ubl_xml(r).replace("<cbc:ID>", "<cbc:ProfileID>TICARIFATURA</cbc:ProfileID><cbc:ID>", 1).encode()
                for _, r in rows.iterrows()]
    ids = list(rows["invoice_id"])
    responses = [APP_RESPONSE.format(date="2026-09-20", code="RED", invoice=ids[0]).encode(),
                 APP_RESPONSE.format(date="2026-09-21", code="KABUL", invoice=ids[1]).encode(),
                 APP_RESPONSE.format(date="2026-09-22", code="KABUL", invoice="YOK-000").encode()]
    assert ubl.document_kind(responses[0]) == "response" and ubl.document_kind(invoices[0]) == "invoice"
    assert ubl.parse_application_response(responses[0]) == [
        {"invoice_id": ids[0], "response": "RED", "response_date": pd.Timestamp("2026-09-20")}]
    df, notes = ingest.load_ubl(invoices + responses, 30)
    by_id = df.set_index("invoice_id")
    assert by_id.at[ids[0], "disputed"] and not by_id.at[ids[1], "disputed"]
    assert by_id.at[ids[1], "efatura_yanit"] == "KABUL" and pd.isna(by_id.at[ids[2], "efatura_yanit"])
    assert any("REDDEDİLDİ" in n for n in notes) and any("1 uygulama yanıtının ait olduğu fatura" in n for n in notes)
    assert any("henüz kabul ya da red yanıtı" in n for n in notes)                    # ids[2] yanıt bekliyor
    assert "Fiyat sözleşmeye aykırı" not in df.to_csv()                              # red nedeni saklanmaz
    # Sonra gelen yanıt öncekinin yerine geçer.
    later = APP_RESPONSE.format(date="2026-09-25", code="KABUL", invoice=ids[0]).encode()
    df2, _ = ingest.load_ubl(invoices + responses + [later], 30)
    assert not df2.set_index("invoice_id").at[ids[0], "disputed"]
