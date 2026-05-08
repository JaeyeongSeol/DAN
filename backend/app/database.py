from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "dan.db"


def get_connection() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return dict(row)


def rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS notes (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              title TEXT NOT NULL,
              content TEXT NOT NULL,
              source TEXT NOT NULL DEFAULT 'manual',
              created_at TEXT NOT NULL DEFAULT (datetime('now')),
              updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS tasks (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              title TEXT NOT NULL,
              description TEXT NOT NULL DEFAULT '',
              due_date TEXT,
              priority TEXT NOT NULL DEFAULT 'medium',
              status TEXT NOT NULL DEFAULT 'open',
              source_note_id INTEGER,
              source_ai_suggestion_id INTEGER,
              created_at TEXT NOT NULL DEFAULT (datetime('now')),
              updated_at TEXT NOT NULL DEFAULT (datetime('now')),
              FOREIGN KEY (source_note_id) REFERENCES notes(id) ON DELETE SET NULL,
              FOREIGN KEY (source_ai_suggestion_id) REFERENCES ai_suggestions(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS ai_suggestions (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              note_id INTEGER,
              type TEXT NOT NULL,
              title TEXT NOT NULL,
              content TEXT NOT NULL,
              raw_payload TEXT NOT NULL DEFAULT '{}',
              status TEXT NOT NULL DEFAULT 'draft',
              created_at TEXT NOT NULL DEFAULT (datetime('now')),
              FOREIGN KEY (note_id) REFERENCES notes(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS uploads (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              filename TEXT NOT NULL,
              kind TEXT NOT NULL,
              content TEXT NOT NULL DEFAULT '',
              transcript TEXT NOT NULL DEFAULT '',
              created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS transcripts (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              upload_id INTEGER,
              note_id INTEGER,
              text TEXT NOT NULL,
              duration_seconds REAL,
              created_at TEXT NOT NULL DEFAULT (datetime('now')),
              FOREIGN KEY (upload_id) REFERENCES uploads(id) ON DELETE CASCADE,
              FOREIGN KEY (note_id) REFERENCES notes(id) ON DELETE SET NULL
            );
            """
        )
        try:
            conn.executescript(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS notes_fts
                USING fts5(title, content, note_id UNINDEXED);

                CREATE TRIGGER IF NOT EXISTS notes_ai AFTER INSERT ON notes BEGIN
                  INSERT INTO notes_fts(rowid, title, content, note_id)
                  VALUES (new.id, new.title, new.content, new.id);
                END;

                CREATE TRIGGER IF NOT EXISTS notes_ad AFTER DELETE ON notes BEGIN
                  INSERT INTO notes_fts(notes_fts, rowid, title, content, note_id)
                  VALUES('delete', old.id, old.title, old.content, old.id);
                END;

                CREATE TRIGGER IF NOT EXISTS notes_au AFTER UPDATE ON notes BEGIN
                  INSERT INTO notes_fts(notes_fts, rowid, title, content, note_id)
                  VALUES('delete', old.id, old.title, old.content, old.id);
                  INSERT INTO notes_fts(rowid, title, content, note_id)
                  VALUES (new.id, new.title, new.content, new.id);
                END;
                """
            )
        except sqlite3.OperationalError:
            # Some SQLite builds omit FTS5. Search falls back to LIKE queries.
            pass


def create_note(title: str, content: str, source: str = "manual") -> dict[str, Any]:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO notes (title, content, source)
            VALUES (?, ?, ?)
            """,
            (title, content, source),
        )
        row = conn.execute("SELECT * FROM notes WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return row_to_dict(row) or {}


def list_notes(query: str | None = None) -> list[dict[str, Any]]:
    with get_connection() as conn:
        if query:
            like = f"%{query}%"
            try:
                rows = conn.execute(
                    """
                    SELECT notes.*
                    FROM notes_fts
                    JOIN notes ON notes.id = notes_fts.note_id
                    WHERE notes_fts MATCH ?
                    ORDER BY notes.updated_at DESC
                    """,
                    (query,),
                ).fetchall()
            except sqlite3.OperationalError:
                rows = conn.execute(
                    """
                    SELECT * FROM notes
                    WHERE title LIKE ? OR content LIKE ?
                    ORDER BY updated_at DESC
                    """,
                    (like, like),
                ).fetchall()
            return rows_to_dicts(rows)

        rows = conn.execute("SELECT * FROM notes ORDER BY updated_at DESC").fetchall()
        return rows_to_dicts(rows)


def get_note(note_id: int) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
        return row_to_dict(row)


def update_note(note_id: int, title: str, content: str, source: str | None = None) -> dict[str, Any] | None:
    current = get_note(note_id)
    if current is None:
        return None
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE notes
            SET title = ?, content = ?, source = COALESCE(?, source), updated_at = datetime('now')
            WHERE id = ?
            """,
            (title, content, source, note_id),
        )
    return get_note(note_id)


def delete_note(note_id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        return cursor.rowcount > 0


def clear_mind() -> dict[str, int]:
    with get_connection() as conn:
        counts = {
            "tasks": conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0],
            "ai_suggestions": conn.execute("SELECT COUNT(*) FROM ai_suggestions").fetchone()[0],
            "transcripts": conn.execute("SELECT COUNT(*) FROM transcripts").fetchone()[0],
            "uploads": conn.execute("SELECT COUNT(*) FROM uploads").fetchone()[0],
            "notes": conn.execute("SELECT COUNT(*) FROM notes").fetchone()[0],
        }
        conn.execute("DROP TRIGGER IF EXISTS notes_ai")
        conn.execute("DROP TRIGGER IF EXISTS notes_ad")
        conn.execute("DROP TRIGGER IF EXISTS notes_au")
        conn.execute("DROP TABLE IF EXISTS notes_fts")
        conn.execute("DELETE FROM tasks")
        conn.execute("DELETE FROM ai_suggestions")
        conn.execute("DELETE FROM transcripts")
        conn.execute("DELETE FROM uploads")
        conn.execute("DELETE FROM notes")
        conn.execute(
            """
            DELETE FROM sqlite_sequence
            WHERE name IN ('notes', 'tasks', 'ai_suggestions', 'uploads', 'transcripts')
            """
        )
    init_db()
    return counts


def create_task(
    title: str,
    description: str = "",
    due_date: str | None = None,
    priority: str = "medium",
    status: str = "open",
    source_note_id: int | None = None,
    source_ai_suggestion_id: int | None = None,
) -> dict[str, Any]:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO tasks (
              title, description, due_date, priority, status,
              source_note_id, source_ai_suggestion_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (title, description, due_date, priority, status, source_note_id, source_ai_suggestion_id),
        )
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return row_to_dict(row) or {}


def list_tasks() -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM tasks ORDER BY status ASC, created_at DESC").fetchall()
        return rows_to_dicts(rows)


def get_task(task_id: int) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        return row_to_dict(row)


def update_task(
    task_id: int,
    title: str,
    description: str,
    due_date: str | None,
    priority: str,
    status: str,
) -> dict[str, Any] | None:
    current = get_task(task_id)
    if current is None:
        return None
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE tasks
            SET title = ?, description = ?, due_date = ?, priority = ?, status = ?, updated_at = datetime('now')
            WHERE id = ?
            """,
            (title, description, due_date, priority, status, task_id),
        )
    return get_task(task_id)


def delete_task(task_id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        return cursor.rowcount > 0


def create_ai_suggestion(
    suggestion_type: str,
    title: str,
    content: str,
    note_id: int | None = None,
    raw_payload: dict[str, Any] | None = None,
    status: str = "draft",
) -> dict[str, Any]:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO ai_suggestions (note_id, type, title, content, raw_payload, status)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (note_id, suggestion_type, title, content, json.dumps(raw_payload or {}), status),
        )
        row = conn.execute("SELECT * FROM ai_suggestions WHERE id = ?", (cursor.lastrowid,)).fetchone()
        item = row_to_dict(row) or {}
        if item:
            item["raw_payload"] = json.loads(item.get("raw_payload") or "{}")
        return item


def get_ai_suggestion(suggestion_id: int) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM ai_suggestions WHERE id = ?", (suggestion_id,)).fetchone()
        item = row_to_dict(row)
        if item:
            item["raw_payload"] = json.loads(item.get("raw_payload") or "{}")
        return item


def list_ai_suggestions(note_id: int | None = None) -> list[dict[str, Any]]:
    with get_connection() as conn:
        if note_id:
            rows = conn.execute(
                "SELECT * FROM ai_suggestions WHERE note_id = ? ORDER BY created_at DESC",
                (note_id,),
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM ai_suggestions ORDER BY created_at DESC").fetchall()
    items = rows_to_dicts(rows)
    for item in items:
        item["raw_payload"] = json.loads(item.get("raw_payload") or "{}")
    return items


def set_ai_suggestion_status(suggestion_id: int, status: str) -> dict[str, Any] | None:
    with get_connection() as conn:
        conn.execute("UPDATE ai_suggestions SET status = ? WHERE id = ?", (status, suggestion_id))
    return get_ai_suggestion(suggestion_id)


def create_upload(filename: str, kind: str, content: str = "", transcript: str = "") -> dict[str, Any]:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO uploads (filename, kind, content, transcript)
            VALUES (?, ?, ?, ?)
            """,
            (filename, kind, content, transcript),
        )
        row = conn.execute("SELECT * FROM uploads WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return row_to_dict(row) or {}


def create_transcript(
    text: str,
    upload_id: int | None = None,
    note_id: int | None = None,
    duration_seconds: float | None = None,
) -> dict[str, Any]:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO transcripts (upload_id, note_id, text, duration_seconds)
            VALUES (?, ?, ?, ?)
            """,
            (upload_id, note_id, text, duration_seconds),
        )
        row = conn.execute("SELECT * FROM transcripts WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return row_to_dict(row) or {}


def search_notes_for_answer(question: str, limit: int = 5) -> list[dict[str, Any]]:
    query = question.strip()
    if not query:
        return list_notes()[:limit]
    results = list_notes(query)
    if results:
        return results[:limit]
    words = [word for word in query.split() if len(word) > 2]
    scored: list[tuple[int, dict[str, Any]]] = []
    for note in list_notes():
        haystack = f"{note['title']} {note['content']}".lower()
        score = sum(1 for word in words if word.lower() in haystack)
        if score:
            scored.append((score, note))
    return [note for _, note in sorted(scored, key=lambda item: item[0], reverse=True)[:limit]]
