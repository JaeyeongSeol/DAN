import json
import sys
import os
from pathlib import Path

# Ensure the backend directory is on PYTHONPATH so `import app` works in CI
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import app.database as db


def test_init_db_and_create_note(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    monkeypatch.setattr(db, "DATA_DIR", data_dir)
    monkeypatch.setattr(db, "DB_PATH", data_dir / "test.db")
    # initialize DB and create a note
    db.init_db()
    note = db.create_note("Test Title", "Test content")
    assert note.get("title") == "Test Title"
    notes = db.list_notes()
    assert any(n["title"] == "Test Title" for n in notes)


def test_create_task_and_list(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    monkeypatch.setattr(db, "DATA_DIR", data_dir)
    monkeypatch.setattr(db, "DB_PATH", data_dir / "test.db")
    db.init_db()
    task = db.create_task("Task 1", description="do stuff")
    assert task.get("title") == "Task 1"
    tasks = db.list_tasks()
    assert any(t["title"] == "Task 1" for t in tasks)
