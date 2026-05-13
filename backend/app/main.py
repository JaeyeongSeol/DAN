from __future__ import annotations

from io import BytesIO
from pathlib import Path
import zipfile
import xml.etree.ElementTree as ET
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from . import ai_service, database
from .transcription_service import transcribe_audio

app = FastAPI(title="DAN Ambition API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

AUDIO_UPLOAD_DIR = Path(__file__).resolve().parents[1] / "uploaded_audio"
MAX_FILE_UPLOAD_BYTES = 2 * 1024 * 1024
TEXT_FILE_EXTENSIONS = {
    ".txt",
    ".md",
    ".csv",
    ".json",
    ".html",
    ".htm",
    ".xml",
    ".log",
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".css",
    ".sql",
}
DOCX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
database.init_db()


class NoteIn(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    content: str = ""
    source: str = "manual"


class TaskIn(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    description: str = ""
    due_date: str | None = None
    priority: str = "medium"
    status: str = "open"
    source_note_id: int | None = None
    source_ai_suggestion_id: int | None = None


class AiTextRequest(BaseModel):
    text: str | None = None
    note_id: int | None = None


class AiActionRunRequest(AiTextRequest):
    action_id: str = Field(min_length=1)


class AskRequest(BaseModel):
    question: str = Field(min_length=1)


class TextUploadRequest(BaseModel):
    title: str = "Imported note"
    content: str
    create_note: bool = True


class ApproveSuggestionRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    due_date: str | None = None
    priority: str | None = None


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "ai": {
            "ollama_available": ai_service.ollama_available(),
            "primary_model": ai_service.PRIMARY_MODEL,
            "fallback_model": ai_service.FALLBACK_MODEL,
        },
    }


@app.post("/api/system/clear-mind")
def clear_mind() -> dict[str, Any]:
    removed = database.clear_mind()
    return {
        "status": "cleared",
        "removed": removed,
        "message": "DAN is fresh for the next user.",
    }


@app.get("/api/notes")
def list_notes(q: str | None = None) -> list[dict[str, Any]]:
    return database.list_notes(q)


@app.post("/api/notes")
def create_note(payload: NoteIn) -> dict[str, Any]:
    return database.create_note(payload.title, payload.content, payload.source)


@app.get("/api/notes/{note_id}")
def get_note(note_id: int) -> dict[str, Any]:
    note = database.get_note(note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@app.put("/api/notes/{note_id}")
def update_note(note_id: int, payload: NoteIn) -> dict[str, Any]:
    note = database.update_note(note_id, payload.title, payload.content, payload.source)
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@app.delete("/api/notes/{note_id}")
def delete_note(note_id: int) -> dict[str, bool]:
    if not database.delete_note(note_id):
        raise HTTPException(status_code=404, detail="Note not found")
    return {"deleted": True}


@app.get("/api/tasks")
def list_tasks() -> list[dict[str, Any]]:
    return database.list_tasks()


@app.post("/api/tasks")
def create_task(payload: TaskIn) -> dict[str, Any]:
    return database.create_task(
        title=payload.title,
        description=payload.description,
        due_date=payload.due_date,
        priority=payload.priority,
        status=payload.status,
        source_note_id=payload.source_note_id,
        source_ai_suggestion_id=payload.source_ai_suggestion_id,
    )


@app.put("/api/tasks/{task_id}")
def update_task(task_id: int, payload: TaskIn) -> dict[str, Any]:
    task = database.update_task(
        task_id,
        payload.title,
        payload.description,
        payload.due_date,
        payload.priority,
        payload.status,
    )
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: int) -> dict[str, bool]:
    if not database.delete_task(task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    return {"deleted": True}


def resolve_ai_text(payload: AiTextRequest) -> tuple[str, int | None]:
    if payload.note_id:
        note = database.get_note(payload.note_id)
        if note is None:
            raise HTTPException(status_code=404, detail="Note not found")
        return note["content"], payload.note_id
    return payload.text or "", None


def save_ai_action_result(result: dict[str, Any], note_id: int | None) -> dict[str, Any]:
    if result["suggestion_type"] == "task":
        suggestions = [
            database.create_ai_suggestion(
                suggestion_type="task",
                title=item["title"],
                content=item.get("description", ""),
                note_id=note_id,
                raw_payload={**item, "action_id": result["action_id"], "mode": result["mode"]},
                status="draft",
            )
            for item in result.get("items", [])
        ]
        return {**result, "suggestions": suggestions}

    suggestion = database.create_ai_suggestion(
        suggestion_type=result["suggestion_type"],
        title=result["title"],
        content=result.get("content", ""),
        note_id=note_id,
        raw_payload=result.get("raw_payload", result),
        status="generated",
    )
    return {**result, "suggestion": suggestion, "suggestions": [suggestion]}


@app.get("/api/ai/actions")
def list_ai_actions() -> list[dict[str, str]]:
    return ai_service.list_ai_actions()


@app.post("/api/ai/actions/run")
def run_ai_action(payload: AiActionRunRequest) -> dict[str, Any]:
    text, note_id = resolve_ai_text(payload)
    try:
        result = ai_service.run_ai_action(payload.action_id, text)
    except KeyError as error:
        raise HTTPException(status_code=400, detail="Unknown AI action") from error
    return save_ai_action_result(result, note_id)


@app.post("/api/ai/summarize")
def summarize(payload: AiTextRequest) -> dict[str, Any]:
    text, note_id = resolve_ai_text(payload)
    result = ai_service.summarize_note(text)
    suggestion = database.create_ai_suggestion(
        suggestion_type="summary",
        title="AI summary",
        content=result["summary"],
        note_id=note_id,
        raw_payload=result,
        status="generated",
    )
    return {**result, "suggestion": suggestion}


@app.post("/api/ai/extract-actions")
def extract_actions(payload: AiTextRequest) -> dict[str, Any]:
    text, note_id = resolve_ai_text(payload)
    result = ai_service.extract_action_items(text)
    suggestions = [
        database.create_ai_suggestion(
            suggestion_type="task",
            title=item["title"],
            content=item.get("description", ""),
            note_id=note_id,
            raw_payload=item,
            status="draft",
        )
        for item in result["items"]
    ]
    return {**result, "suggestions": suggestions}


@app.post("/api/ai/rewrite")
def rewrite(payload: AiTextRequest) -> dict[str, Any]:
    text, note_id = resolve_ai_text(payload)
    result = ai_service.rewrite_note(text)
    suggestion = database.create_ai_suggestion(
        suggestion_type="rewrite",
        title="Cleaned note",
        content=result["rewritten"],
        note_id=note_id,
        raw_payload=result,
        status="generated",
    )
    return {**result, "suggestion": suggestion}


@app.post("/api/ai/ask")
def ask(payload: AskRequest) -> dict[str, Any]:
    matches = database.search_notes_for_answer(payload.question)
    result = ai_service.ask_notes(payload.question, matches)
    return {**result, "matches": matches}


@app.get("/api/ai/suggestions")
def list_suggestions(note_id: int | None = None) -> list[dict[str, Any]]:
    return database.list_ai_suggestions(note_id)


@app.post("/api/ai/suggestions/{suggestion_id}/approve")
def approve_suggestion(suggestion_id: int, payload: ApproveSuggestionRequest) -> dict[str, Any]:
    suggestion = database.get_ai_suggestion(suggestion_id)
    if suggestion is None:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    if suggestion["type"] != "task":
        raise HTTPException(status_code=400, detail="Only task suggestions can become tasks")

    raw = suggestion.get("raw_payload") or {}
    task = database.create_task(
        title=payload.title or suggestion["title"],
        description=payload.description if payload.description is not None else suggestion["content"],
        due_date=payload.due_date if payload.due_date is not None else raw.get("due_date"),
        priority=payload.priority or raw.get("priority") or "medium",
        source_note_id=suggestion.get("note_id"),
        source_ai_suggestion_id=suggestion_id,
    )
    database.set_ai_suggestion_status(suggestion_id, "approved")
    return {"task": task, "suggestion": database.get_ai_suggestion(suggestion_id)}


@app.post("/api/ai/suggestions/{suggestion_id}/dismiss")
def dismiss_suggestion(suggestion_id: int) -> dict[str, Any]:
    suggestion = database.set_ai_suggestion_status(suggestion_id, "dismissed")
    if suggestion is None:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    return suggestion


@app.post("/api/uploads/text")
def upload_text(payload: TextUploadRequest) -> dict[str, Any]:
    upload = database.create_upload(payload.title, "text", payload.content, payload.content)
    note = None
    if payload.create_note:
        note = database.create_note(payload.title, payload.content, "upload")
        database.create_transcript(payload.content, upload_id=upload["id"], note_id=note["id"])
    return {"upload": upload, "note": note}


def decode_text_bytes(data: bytes) -> str:
    if not data:
        return ""
    if b"\x00" in data[:4096]:
        raise HTTPException(status_code=415, detail="This looks like a binary file. Try TXT, MD, CSV, JSON, HTML, XML, LOG, code, or DOCX.")
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return data.decode(encoding).strip()
        except UnicodeDecodeError:
            continue
    raise HTTPException(status_code=415, detail="Could not read this file as text.")


def extract_docx_text(data: bytes) -> str:
    try:
        with zipfile.ZipFile(BytesIO(data)) as archive:
            xml_text = archive.read("word/document.xml")
    except (KeyError, zipfile.BadZipFile) as error:
        raise HTTPException(status_code=415, detail="Could not read this DOCX file.") from error

    root = ET.fromstring(xml_text)
    namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    paragraphs: list[str] = []
    for paragraph in root.findall(".//w:p", namespace):
        parts = [node.text for node in paragraph.findall(".//w:t", namespace) if node.text]
        line = "".join(parts).strip()
        if line:
            paragraphs.append(line)
    return "\n".join(paragraphs).strip()


def extract_file_text(filename: str, content_type: str | None, data: bytes) -> tuple[str, str]:
    extension = Path(filename).suffix.lower()
    if len(data) > MAX_FILE_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File is too large for this prototype. Keep uploads under 2 MB.")
    if extension == ".docx" or content_type == DOCX_CONTENT_TYPE:
        return extract_docx_text(data), "docx"
    if extension in TEXT_FILE_EXTENSIONS or (content_type or "").startswith("text/"):
        return decode_text_bytes(data), "file"
    raise HTTPException(status_code=415, detail="Unsupported file type. Use TXT, MD, CSV, JSON, HTML, XML, LOG, code, or DOCX.")


@app.post("/api/uploads/file")
async def upload_file(
    file: UploadFile = File(...),
    title: str | None = Form(None),
    create_note: bool = Form(True),
) -> dict[str, Any]:
    safe_name = Path(file.filename or "uploaded-context.txt").name
    data = await file.read()
    text, kind = extract_file_text(safe_name, file.content_type, data)
    if not text:
        raise HTTPException(status_code=400, detail="The uploaded file did not contain readable text.")

    note_title = (title or Path(safe_name).stem or "Imported file").strip()
    upload = database.create_upload(safe_name, kind, text, text)
    note = None
    if create_note:
        note = database.create_note(note_title, text, "file")
        database.create_transcript(text, upload_id=upload["id"], note_id=note["id"])
    return {
        "upload": upload,
        "note": note,
        "characters": len(text),
        "kind": kind,
    }


@app.post("/api/uploads/audio")
async def upload_audio(
    file: UploadFile = File(...),
    title: str = Form("Recorded note"),
    create_note: bool = Form(True),
) -> dict[str, Any]:
    AUDIO_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = Path(file.filename or "audio.webm").name
    target = AUDIO_UPLOAD_DIR / safe_name
    data = await file.read()
    target.write_bytes(data)

    result = transcribe_audio(target)
    upload = database.create_upload(safe_name, "audio", "", result["text"])
    note = None
    if create_note:
        note = database.create_note(title, result["text"], "audio")
        database.create_transcript(
            result["text"],
            upload_id=upload["id"],
            note_id=note["id"],
            duration_seconds=result.get("duration_seconds"),
        )
    return {"upload": upload, "note": note, "transcription": result}
