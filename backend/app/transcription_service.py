from __future__ import annotations

from pathlib import Path
from typing import Any


def transcribe_audio(file_path: Path) -> dict[str, Any]:
    try:
        from faster_whisper import WhisperModel  # type: ignore

        model = WhisperModel("base", device="cpu", compute_type="int8")
        segments, info = model.transcribe(str(file_path), beam_size=1)
        text = " ".join(segment.text.strip() for segment in segments if segment.text.strip())
        return {
            "mode": "faster-whisper",
            "language": getattr(info, "language", None),
            "duration_seconds": getattr(info, "duration", None),
            "text": text.strip(),
        }
    except Exception as exc:
        return {
            "mode": "mock",
            "language": None,
            "duration_seconds": None,
            "text": (
                "Audio was uploaded successfully, but local transcription is not installed yet. "
                f"Fallback transcript for {file_path.name}: review the recording, summarize it, "
                "and extract any next steps manually or after installing faster-whisper."
            ),
            "error": str(exc),
        }

