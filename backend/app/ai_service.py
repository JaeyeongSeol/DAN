from __future__ import annotations

import json
import os
import re
from typing import Any

import httpx

OLLAMA_HOST = os.getenv("DAN_OLLAMA_HOST", "http://127.0.0.1:11434")
PRIMARY_MODEL = os.getenv("DAN_OLLAMA_MODEL", "gemma4:e2b")
FALLBACK_MODEL = os.getenv("DAN_OLLAMA_FALLBACK_MODEL", "gemma3:1b")

AI_ACTIONS: dict[str, dict[str, str]] = {
    "summarize": {
        "id": "summarize",
        "label": "Summarize",
        "description": "Create a concise overview with the most important points.",
        "suggestion_type": "summary",
        "result_title": "AI summary",
    },
    "bullet_points": {
        "id": "bullet_points",
        "label": "Bullet points",
        "description": "Convert messy notes into clean bullets.",
        "suggestion_type": "bullet_points",
        "result_title": "Bullet point version",
    },
    "steps": {
        "id": "steps",
        "label": "Steps",
        "description": "Turn the note into an ordered process.",
        "suggestion_type": "steps",
        "result_title": "Step-by-step version",
    },
    "explain_deeper": {
        "id": "explain_deeper",
        "label": "Explain deeper",
        "description": "Add context so the note is easier to understand.",
        "suggestion_type": "explanation",
        "result_title": "Deeper explanation",
    },
    "topics": {
        "id": "topics",
        "label": "Topics",
        "description": "Separate the note into topics and subtopics.",
        "suggestion_type": "topics",
        "result_title": "Topic breakdown",
    },
    "study_notes": {
        "id": "study_notes",
        "label": "Study notes",
        "description": "Make review material from the note.",
        "suggestion_type": "study_notes",
        "result_title": "Study notes",
    },
    "extract_actions": {
        "id": "extract_actions",
        "label": "Extract tasks",
        "description": "Find possible tasks for the review queue.",
        "suggestion_type": "task",
        "result_title": "Task suggestions",
    },
    "rewrite": {
        "id": "rewrite",
        "label": "Clean note",
        "description": "Rewrite rough notes into a clearer version.",
        "suggestion_type": "rewrite",
        "result_title": "Cleaned note",
    },
}


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", clean_text(text))
    return [part.strip() for part in parts if part.strip()]


def list_ai_actions() -> list[dict[str, str]]:
    return [
        {
            "id": action["id"],
            "label": action["label"],
            "description": action["description"],
            "suggestion_type": action["suggestion_type"],
        }
        for action in AI_ACTIONS.values()
    ]


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


def run_ai_action(action_id: str, text: str) -> dict[str, Any]:
    action = AI_ACTIONS.get(action_id)
    if action is None:
        raise KeyError(action_id)

    if action_id == "summarize":
        result = summarize_note(text)
        return {
            "action_id": action_id,
            "mode": result["mode"],
            "suggestion_type": action["suggestion_type"],
            "title": action["result_title"],
            "content": result["summary"],
            "raw_payload": result,
        }

    if action_id == "extract_actions":
        result = extract_action_items(text)
        return {
            "action_id": action_id,
            "mode": result["mode"],
            "suggestion_type": action["suggestion_type"],
            "title": action["result_title"],
            "items": result["items"],
            "raw_payload": result,
        }

    if action_id == "rewrite":
        result = rewrite_note(text)
        return {
            "action_id": action_id,
            "mode": result["mode"],
            "suggestion_type": action["suggestion_type"],
            "title": action["result_title"],
            "content": result["rewritten"],
            "raw_payload": result,
        }

    prompt = build_action_prompt(action_id, text)
    ai_text = call_ollama(
        [
            {"role": "system", "content": "You are DAN, a local assistant that transforms notes into useful study and work material."},
            {"role": "user", "content": prompt},
        ]
    )
    mode = "ollama" if ai_text else "mock"
    content = ai_text or build_mock_action_output(action_id, text)
    return {
        "action_id": action_id,
        "mode": mode,
        "suggestion_type": action["suggestion_type"],
        "title": action["result_title"],
        "content": content,
        "raw_payload": {
            "mode": mode,
            "action_id": action_id,
            "content": content,
        },
    }


def build_action_prompt(action_id: str, text: str) -> str:
    instructions = {
        "bullet_points": "Turn this note into clean, grouped bullet points. Keep the original meaning and remove repetition.",
        "steps": "Turn this note into ordered steps. Each step should start with an action verb when possible.",
        "explain_deeper": "Explain this note in more detail for a student who is learning it. Add context, but do not invent facts.",
        "topics": "Separate this note into topics and subtopics. Use short headings and bullets.",
        "study_notes": "Turn this note into study notes with key ideas, important terms, and review questions.",
    }
    instruction = instructions.get(action_id, "Improve this note while preserving the meaning.")
    return f"""
{instruction}

Note:
{text}
""".strip()


def build_mock_action_output(action_id: str, text: str) -> str:
    sentences = split_sentences(text)
    if not sentences:
        return "No note content was provided."

    if action_id == "bullet_points":
        return "\n".join(f"- {sentence}" for sentence in sentences[:8])

    if action_id == "steps":
        return "\n".join(f"{index}. {sentence}" for index, sentence in enumerate(sentences[:8], start=1))

    if action_id == "explain_deeper":
        bullets = "\n".join(f"- {sentence}" for sentence in sentences[1:5])
        return f"This note is mainly about: {sentences[0]}\n\nUseful context:\n{bullets or '- Review the note and identify the missing details.'}"

    if action_id == "topics":
        topic_lines = []
        for index, sentence in enumerate(sentences[:6], start=1):
            heading = clean_text(sentence).split(",")[0][:60].strip(" .:-")
            topic_lines.append(f"Topic {index}: {heading}\n- {sentence}")
        return "\n\n".join(topic_lines)

    if action_id == "study_notes":
        key_ideas = "\n".join(f"- {sentence}" for sentence in sentences[:5])
        return f"Key ideas:\n{key_ideas}\n\nReview questions:\n- What is the main goal of this note?\n- What details need follow-up?\n- What should be done next?"

    return "\n".join(f"- {sentence}" for sentence in sentences[:8])


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
