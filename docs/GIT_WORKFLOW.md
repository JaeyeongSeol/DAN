# Git Workflow

Repo: https://github.com/JaeyeongSeol/DAN

This is the workflow our group will use so we do not overwrite each other's work.

## First time setup

```bash
git clone https://github.com/JaeyeongSeol/DAN.git
cd DAN
```

## Before starting work

Always update your local copy first.

```bash
git checkout main
git pull origin main
```

Then create a branch for your own task.

```bash
git checkout -b feature/short-task-name
```

Examples:

- `feature/ai-summary-action-items`
- `feature/database-schema`
- `feature/backend-routes`
- `feature/frontend-notes-tasks`
- `feature/github-actions`

## While working

Check what changed before committing.

```bash
git status
```

Add and commit your work.

```bash
git add .
git commit -m "Add short description of work"
```

Push your branch to GitHub.

```bash
git push origin feature/short-task-name
```

## Pull requests

After pushing a branch, open a pull request into `main`.

Before merging:

- Make sure the app still runs.
- Make sure tests pass if tests are available.
- Ask at least one teammate to quickly check the pull request.
- Do not merge broken code into `main`.

## Main branch rule

The `main` branch should stay demo-ready. If something is unfinished, it should stay on a feature branch until it works.

## Merge conflict plan

If there is a merge conflict:

1. Tell the group in Discord.
2. Pull the newest `main`.
3. Fix the conflict carefully.
4. Run the app/tests again.
5. Push the fixed branch.

Nobody should force push or delete another person's work unless the group agrees first.

## Team areas

- Mateus: AI helper logic, product scope, AI prompts, AI fallback plan
- Dan Shakya: SQLite database and data access functions
- Daniel Mclean: FastAPI backend routes
- Benny Ma: React frontend
- Jaeyeong Seol: Scrum master, repo setup, CI/CD, integration

