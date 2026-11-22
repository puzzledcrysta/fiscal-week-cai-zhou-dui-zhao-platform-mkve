import sqlite3
from contextlib import contextmanager
from pathlib import Path
from app import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
  id TEXT PRIMARY KEY, source BLOB NOT NULL, book BLOB NOT NULL,
  result TEXT NOT NULL, created TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS alerts (
  key TEXT NOT NULL, start_day TEXT NOT NULL, trigger_day TEXT NOT NULL, end_day TEXT NOT NULL,
  status TEXT NOT NULL, first_run TEXT NOT NULL, last_run TEXT NOT NULL,
  evidence TEXT NOT NULL, corrections TEXT NOT NULL,
  confirmed_run TEXT, confirmed_at TEXT, decision_note TEXT,
  PRIMARY KEY(key, start_day)
);
CREATE TABLE IF NOT EXISTS confirmations (
  run_id TEXT PRIMARY KEY REFERENCES runs(id), created TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS reviews (
  run_id TEXT NOT NULL REFERENCES runs(id), version INTEGER NOT NULL,
  decision TEXT NOT NULL, note TEXT NOT NULL, changed TEXT NOT NULL,
  PRIMARY KEY(run_id, version)
);
"""


@contextmanager
def connection():
    path = Path(settings.DB)
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=10)
    db.row_factory = sqlite3.Row
    try:
        db.execute('PRAGMA foreign_keys = ON')
        db.executescript(SCHEMA)
        with db:
            yield db
    finally:
        db.close()
