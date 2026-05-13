from __future__ import annotations


def summarize_note(text: str) -> str:
    """Temporary AI summary function until Ollama/Gemma is connected."""
    cleaned_text = text.strip()

    if not cleaned_text:
        return "No note text was provided."

    return (
        "Mock summary: this note has been received. "
        "The real Gemma summary will replace this once the local model is connected."
    )


def extract_action_items(text: str) -> list[dict[str, str]]:
    """Temporary action item extractor until Ollama/Gemma is connected."""
    cleaned_text = text.strip()

    if not cleaned_text:
        return []

    return [
        {
            "title": "Review this note and confirm the next step",
            "due_date": "unknown",
            "priority": "medium",
        }
    ]

