from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_note_task_ai_flow() -> None:
    client.post("/api/system/clear-mind")
    note_response = client.post(
        "/api/notes",
        json={
            "title": "Sprint planning",
            "content": "We need to finish the demo tomorrow. Review the slides and submit the proposal Friday.",
        },
    )
    assert note_response.status_code == 200
    note = note_response.json()

    summary_response = client.post("/api/ai/summarize", json={"note_id": note["id"]})
    assert summary_response.status_code == 200
    assert summary_response.json()["summary"]

    action_response = client.post("/api/ai/extract-actions", json={"note_id": note["id"]})
    assert action_response.status_code == 200
    suggestions = action_response.json()["suggestions"]
    assert suggestions

    approve_response = client.post(f"/api/ai/suggestions/{suggestions[0]['id']}/approve", json={})
    assert approve_response.status_code == 200
    assert approve_response.json()["task"]["title"]

    ask_response = client.post("/api/ai/ask", json={"question": "What do we need to finish?"})
    assert ask_response.status_code == 200
    assert "answer" in ask_response.json()


def test_clear_mind_removes_notes_and_tasks() -> None:
    client.post("/api/system/clear-mind")
    client.post("/api/notes", json={"title": "Temporary", "content": "Temporary note"})
    client.post("/api/tasks", json={"title": "Temporary task"})

    response = client.post("/api/system/clear-mind")

    assert response.status_code == 200
    assert client.get("/api/notes").json() == []
    assert client.get("/api/tasks").json() == []


def test_file_upload_creates_note() -> None:
    client.post("/api/system/clear-mind")

    response = client.post(
        "/api/uploads/file",
        data={"title": "Uploaded context", "create_note": "true"},
        files={"file": ("meeting-notes.txt", b"Finish the upload card and test it.", "text/plain")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["characters"] > 0
    assert body["note"]["title"] == "Uploaded context"
    assert "upload card" in body["note"]["content"]
