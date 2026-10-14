"""Onaylanan taslağın kullanıcının kendi e-posta hesabından gönderilmesi.

Gönderim yalnızca kullanıcı panelde düğmeye bastığında yapılır. Parola kaydedilmez;
yalnızca açık oturum boyunca bellekte tutulur.
"""
from __future__ import annotations

import re
import smtplib
import ssl
from dataclasses import dataclass
from email.message import EmailMessage

_ADDRESS = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class MailError(Exception):
    """Kullanıcıya gösterilebilir gönderim hatası."""


@dataclass
class MailConfig:
    host: str
    port: int
    username: str
    password: str
    sender: str = ""          # boşsa kullanıcı adı kullanılır

    @property
    def ready(self) -> bool:
        return bool(self.host and self.port and self.username and self.password)


def is_address(value) -> bool:
    return isinstance(value, str) and bool(_ADDRESS.match(value.strip()))


def send(cfg: MailConfig, to: str, subject: str, body: str) -> None:
    if not cfg.ready:
        raise MailError("E-posta ayarları eksik.")
    if not is_address(to):
        raise MailError("Alıcı adresi geçerli görünmüyor.")
    msg = EmailMessage()
    msg["From"], msg["To"], msg["Subject"] = cfg.sender or cfg.username, to.strip(), subject
    msg.set_content(body)
    try:
        if cfg.port == 465:
            server = smtplib.SMTP_SSL(cfg.host, cfg.port, timeout=20, context=ssl.create_default_context())
        else:
            server = smtplib.SMTP(cfg.host, cfg.port, timeout=20)
            server.starttls(context=ssl.create_default_context())
        with server:
            server.login(cfg.username, cfg.password)
            server.send_message(msg)
    except smtplib.SMTPAuthenticationError as err:
        raise MailError("Giriş reddedildi: kullanıcı adını ve parolayı (ya da uygulama parolasını) kontrol edin.") from err
    except (smtplib.SMTPException, OSError) as err:
        raise MailError(f"E-posta gönderilemedi: {err}") from err
