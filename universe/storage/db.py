import json
import os
import sqlite3
from typing import Optional

DEFAULT_DB_PATH = os.path.join("data", "universe.db")


def _connect(db_path: str) -> sqlite3.Connection:
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tick INTEGER NOT NULL,
            saved_at TEXT NOT NULL DEFAULT (datetime('now')),
            data TEXT NOT NULL
        )
        """
    )
    return conn


def save_snapshot(universe, db_path: str = DEFAULT_DB_PATH) -> None:
    conn = _connect(db_path)
    try:
        payload = json.dumps(universe.to_dict(), ensure_ascii=False)
        conn.execute("INSERT INTO snapshots (tick, data) VALUES (?, ?)", (universe.tick, payload))
        conn.commit()
        conn.execute("""
            DELETE FROM snapshots WHERE id NOT IN (
                SELECT id FROM snapshots ORDER BY id DESC LIMIT 5
            )
        """)
        conn.commit()
    finally:
        conn.close()


def load_latest_snapshot(db_path: str = DEFAULT_DB_PATH) -> Optional[dict]:
    if not os.path.exists(db_path):
        return None
    conn = _connect(db_path)
    try:
        row = conn.execute(
            "SELECT data FROM snapshots ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if row is None:
            return None
        return json.loads(row[0])
    finally:
        conn.close()


def reset(db_path: str = DEFAULT_DB_PATH) -> None:
    if os.path.exists(db_path):
        os.remove(db_path)
