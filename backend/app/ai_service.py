from __future__ import annotations

import json
import os
import re
from typing import Any

import httpx

OLLAMA_HOST = os.getenv("DAN_OLLAMA_HOST", "http://127.0.0.1:11434")
PRIMARY_MODEL = os.getenv("DAN_OLLAMA_MODEL", "gemma3:4b")
FALLBACK_MODEL = os.getenv("DAN_OLLAMA_FALLBACK_MODEL", "gemma3:1b")


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", clean_text(text))
    return [part.strip() for part in parts if part.strip()]


def ollama_available() -> bool:
    try:
        response = httpx.get(f"{OLLAMA_HOST}/api/tags", timeout=1.5)
        return response.status_code == 200
    except httpx.HTTPError:
        return False


def call_ollama(messages: list[dict[str, str]], model: str | None = None) -> str | None:
    mode = os.getenv("DAN_AI_MODE", "auto").lower()
    if mode == "mock":
        return None

    payload = {
        "model": model or PRIMARY_MODEL,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0.2,
            "top_p": 0.9,
        },
    }

    for candidate in [payload["model"], FALLBACK_MODEL]:
        payload["model"] = candidate
        try:
            response = httpx.post(f"{OLLAMA_HOST}/api/chat", json=payload, timeout=45)
            if response.status_code == 404 and candidate != FALLBACK_MODEL:
                continue
            response.raise_for_status()
            data = response.json()
            return data.get("message", {}).get("content", "").strip() or None
        except httpx.HTTPError:
            if candidate == FALLBACK_MODEL:
                return None
    return None


def summarize_note(text: str) -> dict[str, Any]:
    prompt = f"""
Summarize this note for a productivity app.
Return concise Markdown with:
- 1 sentence overview
- 3 to 5 bullets
- risks/blockers if any

Note:
{text}
""".strip()
    ai_text = call_ollama(
        [
            {"role": "system", "content": "You are DAN, a local assistant that turns messy notes into useful work."},
            {"role": "user", "content": prompt},
        ]
    )
    if ai_text:
        return {"mode": "ollama", "summary": ai_text}

    sentences = split_sentences(text)
    overview = sentences[0] if sentences else "No note content was provided."
    bullets = sentences[1:5] or sentences[:3]
    bullet_text = "\n".join(f"- {item}" for item in bullets)
    summary = f"{overview}\n\n{bullet_text}" if bullet_text else overview
    return {"mode": "mock", "summary": summary}


def _parse_json_array(text: str) -> list[dict[str, Any]] | None:
    if not text:
        return None
    match = re.search(r"\[[\s\S]*\]", text)
    candidate = match.group(0) if match else text
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError:
        return None
    if isinstance(parsed, list):
        return [item for item in parsed if isinstance(item, dict)]
    return None


def extract_action_items(text: str) -> dict[str, Any]:
    prompt = f"""
Extract action items from this note.
Return ONLY valid JSON as an array.
Each item must use this shape:
{{"title": "short task", "description": "why it matters", "due_date": null, "priority": "low|medium|high"}}

Note:
{text}
""".strip()
    ai_text = call_ollama(
        [
            {"role": "system", "content": "You extract clean task suggestions. Output JSON only."},
            {"role": "user", "content": prompt},
        ]
    )
    parsed = _parse_json_array(ai_text or "")
    if parsed is not None:
        return {"mode": "ollama", "items": normalize_action_items(parsed)}

    items: list[dict[str, Any]] = []
    markers = ("todo", "to do", "action", "need to", "needs to", "should", "must", "finish", "submit", "review")
    for sentence in split_sentences(text):
        lower = sentence.lower()
        if any(marker in lower for marker in markers):
            title = re.sub(r"^(we|i|you|they)\s+", "", sentence, flags=re.IGNORECASE)
            title = re.sub(r"\b(need to|needs to|should|must|todo|to do|action:?|finish)\b", "", title, flags=re.IGNORECASE)
            title = clean_text(title).strip(" .:-")
            if title:
                items.append(
                    {
                        "title": title[:90],
                        "description": sentence,
                        "due_date": extract_due_date(sentence),
                        "priority": "high" if "tomorrow" in lower or "urgent" in lower else "medium",
                    }
                )

    if not items and clean_text(text):
        items.append(
            {
                "title": "Review this note and decide next steps",
                "description": "DAN did not find an obvious task, so this is a safe review reminder.",
                "due_date": None,
                "priority": "low",
            }
        )
    return {"mode": "mock", "items": normalize_action_items(items)}


def normalize_action_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for item in items:
        title = clean_text(str(item.get("title") or item.get("task") or "Untitled task"))
        description = clean_text(str(item.get("description") or item.get("details") or ""))
        due_date = item.get("due_date") or item.get("deadline") or None
        priority = str(item.get("priority") or "medium").lower()
        if priority not in {"low", "medium", "high"}:
            priority = "medium"
        normalized.append(
            {
                "title": title[:120],
                "description": description,
                "due_date": due_date,
                "priority": priority,
            }
        )
    return normalized


def extract_due_date(text: str) -> str | None:
    lower = text.lower()
    if "tomorrow" in lower:
        return "tomorrow"
    if "friday" in lower:
        return "Friday"
    if "wednesday" in lower:
        return "Wednesday"
    match = re.search(r"\b\d{4}-\d{2}-\d{2}\b", text)
    return match.group(0) if match else None


def rewrite_note(text: str) -> dict[str, Any]:
    prompt = f"""
Clean this note without changing the meaning.
Use readable headings and bullets where helpful.

Note:
{text}
""".strip()
    ai_text = call_ollama(
        [
            {"role": "system", "content": "You rewrite rough notes into clear study or work notes."},
            {"role": "user", "content": prompt},
        ]
    )
    if ai_text:
        return {"mode": "ollama", "rewritten": ai_text}

    sentences = split_sentences(text)
    rewritten = "\n".join(f"- {sentence}" for sentence in sentences) if sentences else ""
    return {"mode": "mock", "rewritten": rewritten or "No content to rewrite."}


def ask_notes(question: str, matched_notes: list[dict[str, Any]]) -> dict[str, Any]:
    context = "\n\n".join(
        f"Title: {note['title']}\nContent: {note['content'][:1500]}"
        for note in matched_notes
    )
    prompt = f"""
Answer the question using only these notes. If the notes do not contain enough information, say what is missing.

Question:
{question}

Notes:
{context}
""".strip()
    ai_text = call_ollama(
        [
            {"role": "system", "content": "You answer questions from the user's local notes. Be concise and grounded."},
            {"role": "user", "content": prompt},
        ]
    )
    if ai_text:
        return {"mode": "ollama", "answer": ai_text}

    if not matched_notes:
        return {"mode": "mock", "answer": "I could not find matching notes yet. Add or import notes first."}
    note_titles = ", ".join(note["title"] for note in matched_notes[:3])
    return {
        "mode": "mock",
        "answer": f"I found related notes: {note_titles}. The best next step is to open those notes and review the highlighted content.",
    }
