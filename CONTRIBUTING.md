# Contributing

## Branching

- Do not push directly to `main`.
- Create a branch from `main`:
  - `feature/<short-description>`
  - `fix/<short-description>`

## Pull requests

- Open a PR into `main`.
- Link the Trello card.
- Keep PRs small and easy to review.
- CI must be green before merging.

## Backend tests

From repo root:

```bash
cd backend
pip install -r requirements.txt -r requirements-dev.txt
pytest
```

