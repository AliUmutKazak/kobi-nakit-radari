"""Kalıcı kayıt (SQLite).

Yüklenen tablolar ve ayarlar burada saklanır; itiraz, ödeme sözü ve gönderilen
hatırlatmalar silinmeyen bir olay günlüğüne yazılır. Fatura dosyası yeniden
yüklense bile olaylar fatura numarası üzerinden korunur.
"""
from __future__ import annotations

import hashlib
import os
import re
import secrets
import sqlite3
from pathlib import Path

import pandas as pd

TABLES = {"invoices": ["issue_date", "due_date", "paid_date", "promised_date"],
          "payments": ["date"], "outflows": ["date"], "cheques": ["date"], "payables": ["date"]}
EVENT_KINDS = ("dispute", "promise", "message", "writeoff")


def default_path() -> Path:
    """Veritabanının yeri. Proje klasörü OneDrive gibi eşitlenen bir yerde olabilir; müşteri verisi
    buluta gitmesin diye varsayılan yer bu bilgisayarın yerel uygulama klasörüdür."""
    if os.environ.get("RADAR_DB"):
        return Path(os.environ["RADAR_DB"])
    base = os.environ.get("LOCALAPPDATA") or Path.home() / ".local" / "share"
    return Path(base) / "KobiRadar" / "radar.db"


DEFAULT_NAME = "İşletmem"
BACKUP_MAGIC = b"KOBIRADAR-YEDEK-1"     # şifreli yedek dosyasının başlığı (sürümlü)


def _backup_key(password: str, salt: bytes) -> bytes:
    """Paroladan 256 bitlik anahtar: scrypt (bellek-yoğun; kaba kuvvet denemelerini pahalılaştırır)."""
    return hashlib.scrypt(password.encode("utf-8"), salt=salt, n=2 ** 15, r=8, p=1, maxmem=64 * 1024 * 1024, dklen=32)


def encrypt_backup(raw: bytes, password: str) -> bytes:
    """AES-256-GCM: içerik hem gizlenir hem de değiştirilirse fark edilir."""
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    if len(password) < 8:
        raise ValueError("Yedek parolası en az 8 karakter olmalı.")
    salt, nonce = os.urandom(16), os.urandom(12)
    return BACKUP_MAGIC + salt + nonce + AESGCM(_backup_key(password, salt)).encrypt(nonce, raw, BACKUP_MAGIC)


def decrypt_backup(blob: bytes, password: str | None) -> bytes:
    """Şifreli yedeği açar; şifresiz (eski) yedek olduğu gibi döner."""
    if not blob.startswith(BACKUP_MAGIC):
        return blob
    from cryptography.exceptions import InvalidTag
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    if not password:
        raise ValueError("Bu yedek şifreli; parolasını girin.")
    head = len(BACKUP_MAGIC)
    salt, nonce, body = blob[head:head + 16], blob[head + 16:head + 28], blob[head + 28:]
    try:
        return AESGCM(_backup_key(password, salt)).decrypt(nonce, body, BACKUP_MAGIC)
    except InvalidTag:
        raise ValueError("Parola yanlış ya da yedek dosyası bozulmuş.") from None
_TR = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")


def businesses_dir() -> Path:
    """Mali müşavir modu: varsayılan veritabanının yanındaki klasörde işletme başına bir dosya."""
    return default_path().parent / "isletmeler"


def list_businesses() -> dict[str, Path]:
    """{görünen ad: veritabanı yolu}. Varsayılan işletme (tek işletmeli kullanım) her zaman ilk sırada."""
    out = {_name(default_path()) or DEFAULT_NAME: default_path()}
    folder = businesses_dir()
    if folder.exists():
        for path in sorted(folder.glob("*.db")):
            out.setdefault(_name(path) or path.stem, path)
    return out


def _name(path: Path) -> str | None:
    if not path.exists():
        return None
    con = sqlite3.connect(path)
    try:
        row = con.execute("SELECT value FROM settings WHERE key = 'business_name'").fetchone()
    except sqlite3.DatabaseError:
        row = None
    finally:
        con.close()
    return row[0] if row else None


def create_business(name: str) -> Path:
    """Yeni işletme için ayrı bir veritabanı açar. Ad zaten varsa hata verir."""
    name = " ".join(str(name).split())
    if not name:
        raise ValueError("İşletme adı boş olamaz.")
    if name in list_businesses():
        raise ValueError(f"'{name}' adlı işletme zaten var.")
    slug = re.sub(r"[^a-z0-9]+", "-", name.translate(_TR).lower()).strip("-")[:40] or "isletme"
    path = businesses_dir() / f"{slug}.db"
    n = 2
    while path.exists():
        path = businesses_dir() / f"{slug}-{n}.db"
        n += 1
    Store(path).set("business_name", name)
    return path


class Store:
    def __init__(self, path=None):
        path = Path(path) if path else default_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self.db = sqlite3.connect(path, check_same_thread=False, timeout=10)
        # Silinen kayıtlar dosyada sıfırlanır (KVKK Kişisel Veri Güvenliği Rehberi: silme, yok etme).
        self.db.execute("PRAGMA secure_delete = ON")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT);
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT NOT NULL, action TEXT NOT NULL, detail TEXT,
                user TEXT);
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT NOT NULL,
                invoice_id TEXT NOT NULL, kind TEXT NOT NULL, value TEXT);
        """)
        self._pilot_table()
        if self.get("business_id") is None:
            # İşletmenin kalıcı kimliği: anonimleştirme anahtarı işletme başına bundan türetilir.
            self.db.execute("INSERT OR IGNORE INTO settings VALUES ('business_id', ?)", (secrets.token_hex(16),))
            self.db.commit()

    PILOT_COLUMNS = ["target", "horizon", "until", "p10", "p50", "p90", "naive_due", "naive_median", "naive_rate",
                     "naive_flat"]

    def _pilot_table(self) -> None:
        """İleriye dönük pilot kayıtları. Hedef: "tahsilat" (açık faturalardan) ya da "kasa" (kapanış kasası).
        İlk sürümün tablosu (hedef sütunu yok) kayıplar olmadan yeni biçime taşınır."""
        ddl = """CREATE TABLE IF NOT EXISTS pilot_records (
            as_of TEXT NOT NULL, target TEXT NOT NULL DEFAULT 'tahsilat', horizon INTEGER NOT NULL, until TEXT NOT NULL,
            p10 REAL, p50 REAL, p90 REAL, naive_due REAL, naive_median REAL, naive_rate REAL, naive_flat REAL,
            opening REAL, meta TEXT, created TEXT NOT NULL, PRIMARY KEY (as_of, target, horizon))"""
        cols = [r[1] for r in self.db.execute("PRAGMA table_info(pilot_records)")]
        if cols and "target" not in cols:
            self.db.execute("ALTER TABLE pilot_records RENAME TO pilot_records_v1")
            self.db.execute(ddl)
            self.db.execute("""INSERT INTO pilot_records (as_of, target, horizon, until, p10, p50, p90, naive_due,
                               naive_median, naive_rate, created)
                               SELECT as_of, 'tahsilat', horizon, until, p10, p50, p90, naive_due, naive_median,
                               naive_rate, created FROM pilot_records_v1""")
            self.db.execute("DROP TABLE pilot_records_v1")
        else:
            self.db.execute(ddl)
        self.db.commit()

    @property
    def business_id(self) -> str:
        return self.get("business_id")

    @property
    def name(self) -> str:
        return self.get("business_name") or DEFAULT_NAME

    def _bump(self):
        self.db.execute("INSERT INTO settings VALUES ('rev', '1') "
                        "ON CONFLICT(key) DO UPDATE SET value = CAST(value AS INTEGER) + 1")
        self.db.commit()

    @property
    def rev(self) -> int:
        """Her yazmada artar; önbelleği geçersiz kılmak için kullanılır."""
        return int(self.get("rev", 0))

    def get(self, key: str, default=None):
        row = self.db.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row[0] if row else default

    def set(self, key: str, value) -> None:
        if str(value) == str(self.get(key)):
            return
        self.db.execute("INSERT INTO settings VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                        (key, str(value)))
        self._bump()

    @staticmethod
    def _check(name: str) -> None:
        if name not in TABLES:          # tablo adı SQL'e yazıldığı için yalnızca bilinen adlar
            raise ValueError(f"Bilinmeyen tablo: {name}")

    def _exists(self, table: str) -> bool:
        return bool(self.db.execute("SELECT 1 FROM sqlite_master WHERE name = ?", (table,)).fetchone())

    def save(self, name: str, df: pd.DataFrame) -> None:
        """Yeni yükleme eskisinin yerine geçer; eskisi bir önceki sürüm olarak saklanır (geri alınabilir)."""
        self._check(name)
        if self._exists(name):
            self.db.execute(f"DROP TABLE IF EXISTS {name}__onceki")
            self.db.execute(f"ALTER TABLE {name} RENAME TO {name}__onceki")
        df.to_sql(name, self.db, if_exists="replace", index=False)
        self.audit("dosya yüklendi", f"{name}: {len(df)} satır")
        self._bump()

    def can_undo(self, name: str) -> bool:
        self._check(name)
        return self._exists(f"{name}__onceki")

    def undo(self, name: str) -> None:
        """Son yüklemeyi geri alır: bir önceki sürüm yeniden geçerli olur."""
        self._check(name)
        if not self.can_undo(name):
            raise ValueError("Geri alınacak önceki yükleme yok.")
        self.db.execute(f"DROP TABLE IF EXISTS {name}")
        self.db.execute(f"ALTER TABLE {name}__onceki RENAME TO {name}")
        self.db.commit()
        self.audit("son yükleme geri alındı", name)
        self._bump()

    def backup_bytes(self) -> bytes:
        """Veritabanının tutarlı bir kopyası (kullanıcının indirip saklaması için)."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            target = sqlite3.connect(Path(tmp) / "yedek.db")
            self.db.backup(target)
            target.close()
            return (Path(tmp) / "yedek.db").read_bytes()

    def restore(self, blob: bytes, password: str | None = None) -> Path:
        """Yedekten geri yükler. Önce mevcut veri aynı klasöre ayrı bir dosya olarak kopyalanır (geri dönüş
        için); yedek, SQLite dosyası olduğu ve ayar tablosunu içerdiği doğrulanmadan yüklenmez."""
        import tempfile
        raw = decrypt_backup(blob, password)
        if not raw.startswith(b"SQLite format 3\x00"):
            raise ValueError("Bu dosya KOBİ Radar yedeği değil.")
        self.audit("yedekten geri yükleme başladı")
        safety = self.path.with_name(f"{self.path.stem}.geri_yukleme_oncesi_{pd.Timestamp.now():%Y%m%d_%H%M%S}.db")
        safety.write_bytes(self.backup_bytes())
        with tempfile.TemporaryDirectory() as tmp:
            src_path = Path(tmp) / "yedek.db"
            src_path.write_bytes(raw)
            src = sqlite3.connect(src_path)
            try:
                if not src.execute("SELECT 1 FROM sqlite_master WHERE name = 'settings'").fetchone():
                    raise ValueError("Yedekte ayar tablosu yok; geri yükleme yapılmadı.")
                src.backup(self.db)
            finally:
                src.close()
        self._pilot_table()
        self.db.executescript("""CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT NOT NULL, action TEXT NOT NULL, detail TEXT, user TEXT);""")
        self.audit("yedekten geri yüklendi", f"önceki veri: {safety.name}")
        self._bump()
        return safety

    def load(self, name: str) -> pd.DataFrame | None:
        self._check(name)
        if not self.db.execute("SELECT 1 FROM sqlite_master WHERE name = ?", (name,)).fetchone():
            return None
        df = pd.read_sql(f"SELECT * FROM {name}", self.db)
        for col in TABLES[name]:
            if col in df:
                df[col] = pd.to_datetime(df[col])
        if "disputed" in df:
            df["disputed"] = df["disputed"].fillna(0).astype(bool)
        if "vkn" in df:
            df["vkn"] = df["vkn"].fillna("").astype(str)
        return df

    def clear(self) -> None:
        """Yüklenen tabloları siler; olay günlüğü ve ayarlar kalır. Silinen sayfalar dosyadan da temizlenir
        (secure_delete + VACUUM): veri yalnızca tablodan değil, diskteki dosyadan da kalkar."""
        for name in TABLES:
            self.db.execute(f"DROP TABLE IF EXISTS {name}")
            self.db.execute(f"DROP TABLE IF EXISTS {name}__onceki")
        self.db.commit()
        self.db.execute("VACUUM")
        self.audit("tablolar silindi")
        self._bump()

    def audit(self, action: str, detail: str = "") -> None:
        """İşlem kaydı (KVKK rehberi: erişim ve log kayıtları). Yalnızca eklenir; uygulamada silme yolu yoktur."""
        self.db.execute("INSERT INTO audit_log (ts, action, detail, user) VALUES (?, ?, ?, ?)",
                        (pd.Timestamp.now().isoformat(timespec="seconds"), action, detail,
                         os.environ.get("USERNAME") or os.environ.get("USER") or ""))
        self.db.commit()

    def audit_log(self, limit: int = 200) -> pd.DataFrame:
        return pd.read_sql("SELECT ts, action, detail, user FROM audit_log ORDER BY id DESC LIMIT ?", self.db,
                           params=(limit,))

    def destroy(self) -> list[Path]:
        """İşletmenin bütün verisini imha eder: veritabanı dosyası ve geri yükleme öncesi kopyaları silinir.
        Önce içerik sıfırlanır (secure_delete + VACUUM), sonra dosyalar kaldırılır. Dönen: silinen dosyalar."""
        for (name,) in self.db.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall():
            if not name.startswith("sqlite_"):
                self.db.execute(f'DROP TABLE IF EXISTS "{name}"')
        self.db.commit()
        self.db.execute("VACUUM")
        self.db.close()
        gone = [self.path, *self.path.parent.glob(f"{self.path.stem}.geri_yukleme_oncesi_*.db")]
        for f in gone:
            f.unlink(missing_ok=True)
        return gone

    def add_event(self, invoice_id: str, kind: str, value: str = "", ts=None) -> None:
        if kind not in EVENT_KINDS:
            raise ValueError(f"Bilinmeyen olay: {kind}")
        ts = pd.Timestamp(ts) if ts is not None else pd.Timestamp.now()
        self.db.execute("INSERT INTO events (ts, invoice_id, kind, value) VALUES (?, ?, ?, ?)",
                        (ts.isoformat(), str(invoice_id), kind, str(value)))
        self._bump()

    def add_pilot_record(self, as_of, record: pd.DataFrame, opening: float | None = None,
                         meta: dict | None = None) -> bool:
        """İleriye dönük pilot kaydı. Kayıt dondurulmuştur: aynı tarih ve hedef için ikinci kez yazılmaz,
        değiştirilmez, "Tabloları sil" ile de silinmez. `meta`: kesim tarihi, veri özeti, yöntem, sürüm,
        eşleşme oranı ve kapsam (sonradan "hangi veriyle, hangi kodla" sorusunu cevaplamak için).
        Önbelleği bozmamak için sürüm numarasını artırmaz."""
        import json
        as_of = f"{pd.Timestamp(as_of):%Y-%m-%d}"
        rec = record.reindex(columns=self.PILOT_COLUMNS)
        rec["target"] = rec["target"].fillna("tahsilat")

        def cell(col, v):
            if v is None or (not isinstance(v, str) and pd.isna(v)):
                return None
            return v if col in ("target", "until") else (int(v) if col == "horizon" else float(v))

        before = self.db.total_changes
        self.db.executemany(
            "INSERT OR IGNORE INTO pilot_records VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [(as_of, *[cell(c, v) for c, v in zip(self.PILOT_COLUMNS, row)],
              None if opening is None else float(opening), json.dumps(meta or {}, ensure_ascii=False, default=str),
              pd.Timestamp.now().isoformat(timespec="seconds"))
             for row in rec.itertuples(index=False)])
        self.db.commit()
        return self.db.total_changes > before

    def pilot_records(self) -> pd.DataFrame:
        return pd.read_sql("SELECT * FROM pilot_records ORDER BY as_of, target, horizon", self.db)

    def events(self) -> pd.DataFrame:
        df = pd.read_sql("SELECT * FROM events ORDER BY id", self.db)
        df["ts"] = pd.to_datetime(df["ts"])
        return df

    def apply_events(self, invoices: pd.DataFrame, as_of) -> pd.DataFrame:
        """Fatura tablosuna, `as_of` tarihine kadarki olayların son durumunu işler."""
        inv = invoices.copy()
        if "disputed" not in inv:
            inv["disputed"] = False
        if "promised_date" not in inv:
            inv["promised_date"] = pd.NaT
        inv["last_contact"] = pd.NaT
        ev = self.events()
        ev = ev[ev["ts"] < pd.Timestamp(as_of) + pd.Timedelta(days=1)]
        last = ev.groupby(["invoice_id", "kind"]).last()
        ids = inv["invoice_id"].astype(str)
        for kind, col, convert in (("dispute", "disputed", lambda v: v == "1"),
                                   ("promise", "promised_date", lambda v: pd.Timestamp(v) if v else pd.NaT)):
            if kind in last.index.get_level_values("kind"):
                values = last.xs(kind, level="kind")["value"].map(convert)
                hit = ids.isin(values.index)
                inv.loc[hit, col] = ids[hit].map(values).to_numpy()
        if "message" in last.index.get_level_values("kind"):
            inv["last_contact"] = ids.map(last.xs("message", level="kind")["ts"])
        # Tahsil edilemez sayılan (silinen) fatura: açık alacaktan ve tahminden çıkar, ödenmiş sayılmaz;
        # modelin "hiç ödenmeme" oranını öğrendiği geçmişte ödenmemiş olarak kalır.
        inv["written_off"] = False
        if "writeoff" in last.index.get_level_values("kind"):
            gone = ids.map(last.xs("writeoff", level="kind")["value"]).eq("1")
            inv.loc[gone, "written_off"] = True
            inv.loc[gone & inv["paid_date"].isna(), "open_amount"] = 0.0
        inv["disputed"] = inv["disputed"].astype(bool)
        inv["promised_date"] = pd.to_datetime(inv["promised_date"])
        return inv
