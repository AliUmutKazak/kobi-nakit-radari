"""Kayıt, yedek, işlem kaydı, parola ve e-posta güvenliği."""
from pathlib import Path

import pandas as pd
import pytest

from radar import pipeline
from radar.synthetic import observe

from conftest import AS_OF


def test_store_persists_tables_and_events(full, tmp_path):
    from radar.store import Store

    obs = observe(full, AS_OF)
    store = Store(tmp_path / "radar.db")
    assert store.load("invoices") is None and store.rev == 0
    store.save("invoices", obs)
    store.set("opening", 1500.0)
    open_ids = list(obs.loc[obs["open_amount"] > 0].sort_values("due_date")["invoice_id"])
    a, b, c = open_ids[0], open_ids[1], open_ids[2]
    store.add_event(a, "dispute", "1", ts="2026-09-20")
    store.add_event(b, "promise", "2026-10-25", ts="2026-09-21")
    store.add_event(c, "message", "taslak metni", ts="2026-09-29")
    store.add_event(a, "dispute", "0", ts="2026-10-05")           # AS_OF'tan sonra: henüz geçerli değil

    again = Store(tmp_path / "radar.db")                           # yeniden açınca her şey yerinde
    inv = again.apply_events(again.load("invoices"), AS_OF).set_index("invoice_id")
    assert len(inv) == len(obs) and float(again.get("opening")) == 1500.0 and again.rev == store.rev > 0
    assert inv["issue_date"].dtype.kind == "M" and inv.at[a, "disputed"] and not inv.at[b, "disputed"]
    assert inv.at[b, "promised_date"] == pd.Timestamp("2026-10-25")
    assert inv.at[c, "last_contact"] == pd.Timestamp("2026-09-29")

    res = pipeline.forecast(inv.reset_index(), AS_OF, 0.0, pd.DataFrame({"date": [], "amount": []}),
                            n_sims=200, include_projected=False)
    ranked = res["ranked"].set_index("invoice_id")
    assert a not in ranked.index and ranked.at[b, "stage"] == "soz"
    assert not ranked.at[c, "actionable"]                          # 2 gün önce yazıldı, bekleme süresinde
    later = again.apply_events(again.load("invoices"), "2026-10-10").set_index("invoice_id")
    assert not later.at[a, "disputed"]


def test_mailer_sends_only_valid_complete_requests(monkeypatch):
    import smtplib

    from radar import mailer

    sent = []

    class FakeSMTP:
        def __init__(self, host, port, **kw):
            self.host, self.port = host, port
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def starttls(self, **kw): sent.append("tls")
        def login(self, user, password):
            if password == "yanlis":
                raise smtplib.SMTPAuthenticationError(535, b"bad")
        def send_message(self, msg): sent.append(msg)

    monkeypatch.setattr(smtplib, "SMTP", FakeSMTP)
    cfg = mailer.MailConfig("smtp.example.com", 587, "ben@example.com", "gizli")
    mailer.send(cfg, " musteri@firma.com.tr ", "Fatura hakkında", "Merhaba, ödeme hatırlatması.")
    assert sent[0] == "tls" and sent[1]["To"] == "musteri@firma.com.tr" and sent[1]["From"] == "ben@example.com"
    assert "ödeme hatırlatması" in sent[1].get_content()
    with pytest.raises(mailer.MailError, match="Alıcı"):
        mailer.send(cfg, "adres-degil", "k", "m")
    with pytest.raises(mailer.MailError, match="eksik"):
        mailer.send(mailer.MailConfig("smtp.example.com", 587, "ben@example.com", ""), "a@b.co", "k", "m")
    with pytest.raises(mailer.MailError, match="Giriş reddedildi"):
        mailer.send(mailer.MailConfig("smtp.example.com", 587, "ben@example.com", "yanlis"), "a@b.co", "k", "m")
    assert len(sent) == 3                                  # hatalı denemelerde hiçbir ileti gitmedi


def test_security_hardening(tmp_path, monkeypatch):
    import tomllib

    from radar import ubl
    from radar.store import Store, default_path

    cfg = tomllib.loads((Path(__file__).parents[1] / ".streamlit" / "config.toml").read_text(encoding="utf-8"))
    assert cfg["server"]["address"] == "127.0.0.1" and cfg["browser"]["gatherUsageStats"] is False

    bomb = """<?xml version="1.0"?><!DOCTYPE x [<!ENTITY a "aaaaaaaaaa"><!ENTITY b "&a;&a;&a;&a;&a;&a;&a;&a;&a;&a;">]>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2">&b;</Invoice>"""
    with pytest.raises(Exception, match="(?i)entit"):
        ubl.parse_invoice(bomb)

    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.delenv("RADAR_DB", raising=False)
    assert default_path() == tmp_path / "KobiRadar" / "radar.db"
    # Veritabanı bulutla eşitlenen bir klasördeyse panel uyarır (müşteri verisi buluta kopyalanmasın).
    from radar.store import synced_folder
    monkeypatch.setenv("OneDrive", str(tmp_path / "OneDrive"))
    assert synced_folder(tmp_path / "OneDrive" / "Masaüstü" / "radar.db") == str(tmp_path / "OneDrive")
    assert synced_folder(tmp_path / "Dropbox" / "radar.db") == "Dropbox"
    assert synced_folder(default_path()) is None
    store = Store(tmp_path / "x.db")
    with pytest.raises(ValueError):
        store.load("invoices; DROP TABLE settings")
    with pytest.raises(ValueError):
        store.add_event("A1", "hack")


def test_mail_headers_cannot_be_injected(monkeypatch):
    import smtplib

    from radar import mailer

    sent = []

    class FakeSMTP:
        def __init__(self, *a, **kw): pass
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def starttls(self, **kw): pass
        def login(self, *a): pass
        def send_message(self, msg): sent.append(msg)

    monkeypatch.setattr(smtplib, "SMTP", FakeSMTP)
    cfg = mailer.MailConfig("smtp.example.com", 587, "ben@example.com", "x")
    mailer.send(cfg, "a@b.co", "Fatura A1\nBcc: kurban@example.com", "metin")
    assert sent[0]["Bcc"] is None and "\n" not in sent[0]["Subject"]


def test_upload_undo_and_backup(tmp_path):
    import sqlite3

    from radar.store import Store

    store = Store(tmp_path / "s.db")
    store.save("invoices", pd.DataFrame({"invoice_id": ["A"], "amount": [1.0]}))
    assert not store.can_undo("invoices")
    store.save("invoices", pd.DataFrame({"invoice_id": ["B", "C"], "amount": [2.0, 3.0]}))
    assert store.can_undo("invoices") and list(store.load("invoices")["invoice_id"]) == ["B", "C"]
    store.undo("invoices")
    assert list(store.load("invoices")["invoice_id"]) == ["A"] and not store.can_undo("invoices")
    copy = tmp_path / "yedek.db"
    copy.write_bytes(store.backup_bytes())
    assert sqlite3.connect(copy).execute("SELECT invoice_id FROM invoices").fetchall() == [("A",)]


def test_accountant_mode_keeps_businesses_apart(tmp_path, monkeypatch):
    from radar import anonymize
    from radar.store import Store, create_business, list_businesses

    monkeypatch.setenv("RADAR_DB", str(tmp_path / "radar.db"))
    main = Store()
    main.save("invoices", pd.DataFrame({"invoice_id": ["A"], "amount": [1.0]}))
    assert list(list_businesses()) == ["İşletmem"]
    path = create_business("  Çağrı   Gıda Ltd. ")
    assert path.name == "cagri-gida-ltd.db" and list(list_businesses()) == ["İşletmem", "Çağrı Gıda Ltd."]
    with pytest.raises(ValueError):
        create_business("Çağrı Gıda Ltd.")
    other = Store(path)
    assert other.load("invoices") is None and other.name == "Çağrı Gıda Ltd."     # veriler ayrı
    assert main.business_id != other.business_id and Store().business_id == main.business_id   # kimlik kalıcı
    master = "m" * 64
    a, b = (anonymize.business_key(master, s.business_id) for s in (main, other))
    assert a != b and anonymize.pseudonym(a, "X") != anonymize.pseudonym(b, "X")      # işletmeler arası eşleşmez


def test_encrypted_backup_roundtrip_and_restore(tmp_path):
    from radar.store import Store, decrypt_backup, encrypt_backup

    store = Store(tmp_path / "a.db")
    store.save("invoices", pd.DataFrame({"invoice_id": ["A"], "amount": [1.0]}))
    store.set("seller", "Örnek A.Ş.")
    blob = encrypt_backup(store.backup_bytes(), "uzun-parola-1")
    assert "Örnek A.Ş.".encode() in store.backup_bytes() and "Örnek A.Ş.".encode() not in blob   # şifreli
    with pytest.raises(ValueError):
        decrypt_backup(blob, "yanlis-parola")
    with pytest.raises(ValueError):
        encrypt_backup(b"x", "kisa")
    other = Store(tmp_path / "b.db")
    other.save("invoices", pd.DataFrame({"invoice_id": ["Z", "Y"], "amount": [9.0, 8.0]}))
    safety = other.restore(blob, "uzun-parola-1")
    assert list(other.load("invoices")["invoice_id"]) == ["A"] and other.get("seller") == "Örnek A.Ş."
    assert safety.exists() and len(Store(safety).load("invoices")) == 2           # önceki veri kenarda
    with pytest.raises(ValueError):
        other.restore(b"rastgele bayt", None)


def test_audit_log_secure_delete_destroy_and_panel_password(tmp_path, monkeypatch):
    from radar import access
    from radar.store import Store

    monkeypatch.setenv("RADAR_DB", str(tmp_path / "radar.db"))
    store = Store(tmp_path / "radar.db")
    secret = "GIZLIMUSTERI-ABC-12345"
    store.save("invoices", pd.DataFrame({"invoice_id": ["A"], "customer_name": [secret], "amount": [1.0]}))
    store.clear()
    assert secret.encode() not in (tmp_path / "radar.db").read_bytes()          # silinen veri dosyada da yok
    log = store.audit_log()
    assert list(log["action"][:2]) == ["tablolar silindi", "dosya yüklendi"]
    (tmp_path / "radar.geri_yukleme_oncesi_20260101_000000.db").write_bytes(b"x")
    gone = store.destroy()
    assert len(gone) == 2 and not any(f.exists() for f in gone)
    assert not access.enabled() and access.check("ne olursa")
    with pytest.raises(ValueError):
        access.set_password("kisa")
    access.set_password("uzun-parola-9")
    assert access.enabled() and access.check("uzun-parola-9") and not access.check("yanlis-parola")
    assert "uzun-parola-9" not in access.password_file().read_text(encoding="utf-8")
    access.remove("uzun-parola-9")
    assert not access.enabled()


def test_panel_password_gate(tmp_path, monkeypatch):
    from streamlit.testing.v1 import AppTest

    from radar import access

    root = Path(__file__).parents[1]
    monkeypatch.chdir(root)
    monkeypatch.setenv("RADAR_DB", str(tmp_path / "panel.db"))
    access.set_password("dogru-parola-1")
    at = AppTest.from_file(str(root / "app.py"), default_timeout=300).run()
    assert len(at.metric) == 0 and at.text_input[0].label == "Panel parolası"
    at.text_input[0].set_value("yanlis-parola").run()
    at.button[0].click().run()
    assert any("Parola yanlış" in e.value for e in at.error) and len(at.metric) == 0
    at.text_input[0].set_value("dogru-parola-1").run()
    at.button[0].click().run()
    assert not at.exception and len(at.metric) == 6                       # demo şirket açıldı
