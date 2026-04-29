# DAN (ACIT 2911)

Notes + tasks app with local AI helpers (Ollama + Gemma) to summarize notes and extract action items (user-approved before saving).

## Tech stack

- Frontend: React (JavaScript)
- Backend: FastAPI (Python)
- Database: SQLite
- AI: Ollama + Gemma (via Python)
- Testing: Pytest
- CI: GitHub Actions

## MVP

- Notes CRUD
- Tasks CRUD
- Search/filter
- AI: summarize note
- AI: extract action items
- User confirms AI-generated tasks before saving

## Repo layout

```
backend/     FastAPI app + tests
frontend/    React app
docs/        proposal/team charter/presentation notes
```