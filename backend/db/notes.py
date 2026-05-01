from __future__ import annotations

import sqlite3


def create_note(conn: sqlite3.Connection, title: str, content: str, tags: str = "") -> int:
    cur = conn.execute(
        "INSERT INTO notes (title, content, tags) VALUES (?, ?, ?)",
        (title, content, tags),
    )
    conn.commit()
    return int(cur.lastrowid)


def get_note(conn: sqlite3.Connection, note_id: int) -> dict | None:
    row = conn.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
    return dict(row) if row else None


def list_notes(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute("SELECT * FROM notes ORDER BY created_at DESC").fetchall()
    return [dict(r) for r in rows]


def update_note(conn: sqlite3.Connection, note_id: int, title: str, content: str, tags: str = "") -> bool:
    cur = conn.execute(
        "UPDATE notes SET title = ?, content = ?, tags = ?, updated_at = datetime('now') WHERE id = ?",
        (title, content, tags, note_id),
    )
    conn.commit()
    return cur.rowcount > 0


def delete_note(conn: sqlite3.Connection, note_id: int) -> bool:
    cur = conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    conn.commit()
    return cur.rowcount > 0

