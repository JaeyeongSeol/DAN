from __future__ import annotations

import sqlite3


def create_task(
    conn: sqlite3.Connection,
    title: str,
    description: str = "",
    due_date: str | None = None,
    source_note_id: int | None = None,
) -> int:
    cur = conn.execute(
        "INSERT INTO tasks (title, description, due_date, source_note_id) VALUES (?, ?, ?, ?)",
        (title, description, due_date, source_note_id),
    )
    conn.commit()
    return int(cur.lastrowid)


def get_task(conn: sqlite3.Connection, task_id: int) -> dict | None:
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return dict(row) if row else None


def list_tasks(conn: sqlite3.Connection, include_completed: bool = True) -> list[dict]:
    if include_completed:
        rows = conn.execute("SELECT * FROM tasks ORDER BY created_at DESC").fetchall()
    else:
        rows = conn.execute("SELECT * FROM tasks WHERE completed = 0 ORDER BY created_at DESC").fetchall()
    return [dict(r) for r in rows]


def set_task_completed(conn: sqlite3.Connection, task_id: int, completed: bool) -> bool:
    cur = conn.execute(
        "UPDATE tasks SET completed = ?, updated_at = datetime('now') WHERE id = ?",
        (1 if completed else 0, task_id),
    )
    conn.commit()
    return cur.rowcount > 0


def delete_task(conn: sqlite3.Connection, task_id: int) -> bool:
    cur = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    return cur.rowcount > 0

