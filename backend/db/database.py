import os
import sqlite3
from pathlib import Path


DEFAULT_DB_PATH = os.environ.get("DAN_DB_PATH", "dan.sqlite3")


def get_connection(db_path: str | None = None) -> sqlite3.Connection:
    path = db_path or DEFAULT_DB_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str | None = None) -> None:
    conn = get_connection(db_path)
    schema_path = Path(__file__).with_name("schema.sql")
    conn.executescript(schema_path.read_text(encoding="utf-8"))
    conn.commit()
    conn.close()

