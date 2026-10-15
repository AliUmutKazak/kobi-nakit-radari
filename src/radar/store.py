"""Kalıcı kayıt (SQLite).

Yüklenen tablolar ve ayarlar burada saklanır; itiraz, ödeme sözü ve gönderilen
hatırlatmalar silinmeyen bir olay günlüğüne yazılır. Fatura dosyası yeniden
yüklense bile olaylar fatura numarası üzerinden korunur.
"""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path

import pandas as pd

TABLES = {"invoices": ["issue_date", "due_date", "paid_date", "promised_date"],
          "payments": ["date"], "outflows": ["date"], "cheques": ["date"], "payables": ["date"]}
EVENT_KINDS = ("dispute", "promise", "message")


def default_path() -> Path:
    """Veritabanının yeri. Proje klasörü OneDrive gibi eşitlenen bir yerde olabilir; müşteri verisi
    buluta gitmesin diye varsayılan yer bu bilgisayarın yerel uygulama klasörüdür."""
    if os.environ.get("RADAR_DB"):
        return Path(os.environ["RADAR_DB"])
    base = os.environ.get("LOCALAPPDATA") or Path.home() / ".local" / "share"
    return Path(base) / "KobiRadar" / "radar.db"


class Store:
    def __init__(self, path=None):
        path = Path(path) if path else default_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self.db = sqlite3.connect(path, check_same_thread=False, timeout=10)
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT);
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT NOT NULL,
                invoice_id TEXT NOT NULL, kind TEXT NOT NULL, value TEXT);
            CREATE TABLE IF NOT EXISTS pilot_records (
                as_of TEXT NOT NULL, horizon INTEGER NOT NULL, until TEXT NOT NULL,
                p10 REAL, p50 REAL, p90 REAL, naive_due REAL, naive_median REAL, naive_rate REAL,
                created TEXT NOT NULL, PRIMARY KEY (as_of, horizon));
        """)

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
        self._bump()

    def backup_bytes(self) -> bytes:
        """Veritabanının tutarlı bir kopyası (kullanıcının indirip saklaması için)."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            target = sqlite3.connect(Path(tmp) / "yedek.db")
            self.db.backup(target)
            target.close()
            return (Path(tmp) / "yedek.db").read_bytes()

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
        """Yüklenen tabloları siler; olay günlüğü ve ayarlar kalır."""
        for name in TABLES:
            self.db.execute(f"DROP TABLE IF EXISTS {name}")
            self.db.execute(f"DROP TABLE IF EXISTS {name}__onceki")
        self._bump()

    def add_event(self, invoice_id: str, kind: str, value: str = "", ts=None) -> None:
        if kind not in EVENT_KINDS:
            raise ValueError(f"Bilinmeyen olay: {kind}")
        ts = pd.Timestamp(ts) if ts is not None else pd.Timestamp.now()
        self.db.execute("INSERT INTO events (ts, invoice_id, kind, value) VALUES (?, ?, ?, ?)",
                        (ts.isoformat(), str(invoice_id), kind, str(value)))
        self._bump()

    def add_pilot_record(self, as_of, record: pd.DataFrame) -> bool:
        """İleriye dönük pilot kaydı. Kayıt dondurulmuştur: aynı tarih için ikinci kez yazılmaz, değiştirilmez,
        "Tabloları sil" ile de silinmez. Önbelleği bozmamak için sürüm numarasını artırmaz."""
        as_of = f"{pd.Timestamp(as_of):%Y-%m-%d}"
        cols = ["horizon", "until", "p10", "p50", "p90", "naive_due", "naive_median", "naive_rate"]
        before = self.db.total_changes
        self.db.executemany(
            "INSERT OR IGNORE INTO pilot_records VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [(as_of, *[None if pd.isna(v) else (int(v) if c == "horizon" else v if c == "until" else float(v))
                       for c, v in zip(cols, row)], pd.Timestamp.now().isoformat(timespec="seconds"))
             for row in record[cols].itertuples(index=False)])
        self.db.commit()
        return self.db.total_changes > before

    def pilot_records(self) -> pd.DataFrame:
        return pd.read_sql("SELECT * FROM pilot_records ORDER BY as_of, horizon", self.db)

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
        inv["disputed"] = inv["disputed"].astype(bool)
        inv["promised_date"] = pd.to_datetime(inv["promised_date"])
        return inv
