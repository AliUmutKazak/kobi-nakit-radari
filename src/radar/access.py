"""Panel parolası (KVKK Kişisel Veri Güvenliği Rehberi: kullanıcı hesap yönetimi, yetki kontrolü).

Panel yalnızca bu bilgisayardan açılır (127.0.0.1); Windows hesabı birinci korumadır. Ortak kullanılan
bilgisayarlarda (ör. mali müşavir bürosu) isteğe bağlı ikinci bir parola istenebilir. Parola saklanmaz;
yalnızca tuzlu scrypt özeti, bütün işletmeler için ortak bir dosyada tutulur. Parola unutulursa dosya
silinerek kaldırılır (bilgisayara erişimi olan kişi zaten dosyalara erişebildiği için bu ek bir açık değildir;
parola, açık bırakılmış oturumda başkasının paneli görmesini önler).
"""
from __future__ import annotations

import hashlib
import hmac
import os
from pathlib import Path

from .store import default_path

MIN_LENGTH = 8


def password_file() -> Path:
    return default_path().parent / "panel_parolasi.txt"


def _hash(password: str, salt: bytes) -> bytes:
    return hashlib.scrypt(password.encode("utf-8"), salt=salt, n=2 ** 14, r=8, p=1, dklen=32)


def enabled() -> bool:
    return password_file().exists()


def set_password(password: str) -> None:
    if len(password) < MIN_LENGTH:
        raise ValueError(f"Parola en az {MIN_LENGTH} karakter olmalı.")
    salt = os.urandom(16)
    path = password_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(salt.hex() + ":" + _hash(password, salt).hex(), encoding="utf-8")


def check(password: str) -> bool:
    if not enabled():
        return True
    salt_hex, digest_hex = password_file().read_text(encoding="utf-8").strip().split(":")
    return hmac.compare_digest(_hash(password, bytes.fromhex(salt_hex)).hex(), digest_hex)


def remove(password: str) -> None:
    if not check(password):
        raise ValueError("Parola yanlış.")
    password_file().unlink(missing_ok=True)
