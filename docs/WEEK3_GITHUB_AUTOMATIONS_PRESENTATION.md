# Week 3 GitHub Automations Presentation

## What We Added

The repo now has three GitHub Actions workflows that show both code quality and team-process automation:

1. `CI` runs automatically on every pull request and every push to `main`.
2. `PR Checklist` checks that pull requests follow the team's required process.
3. `Demo Smoke Test` runs for backend-related pull requests, can be run manually before presenting, and also runs weekly on Friday morning.

## What To Show On GitHub

1. Open the repo: `https://github.com/JaeyeongSeol/DAN`
2. Click the `Actions` tab.
3. Show the `CI` workflow and explain the two jobs:
   - `backend-tests` installs Python dependencies and runs Pytest.
   - `frontend-build` installs the React/Vite app and runs `npm run build`.
4. Show the `PR Checklist` workflow:
   - It makes sure the PR has summary, changes, test steps, Trello info, and a proper branch name.
5. Show the `Demo Smoke Test` workflow:
   - Open the PR check if it already ran, or click `Run workflow` after it is merged to `main`.
   - Explain that it starts the backend in mock AI mode and calls `/health`.

## Short Speaking Script

For Week 3, our group added GitHub Actions so GitHub can check our project automatically instead of relying only on someone testing on their laptop.

The first workflow is CI. It runs whenever we open a pull request or push to main. It installs the backend dependencies, runs Pytest, and builds the React frontend. We also set `DAN_AI_MODE=mock`, because GitHub does not have our local Ollama or Gemma model installed. That means the pipeline can still test the app logic without depending on a local AI setup.

The second workflow is PR Checklist. This is more about our Agile process. It checks that every pull request has a summary, a list of changes, test steps, a Trello card, and a branch name like `feature/...` or `fix/...`. So it automates the team agreement that we should not merge vague work.

The third workflow is Demo Smoke Test. It runs on backend-related pull requests, and before a demo we can also run it manually from the Actions tab. It starts the FastAPI backend in GitHub Actions and calls `/health`. This proves the app can actually boot, not just pass unit tests.

So the main idea is: CI protects the code, PR Checklist protects the team workflow, and Demo Smoke Test protects the presentation.

## If Something Fails During The Presentation

Say this calmly:

The failure is still useful because GitHub Actions is showing exactly where the project is not ready. If Pytest fails, it means a backend behavior changed. If the frontend build fails, it means a React or Vite issue needs fixing. If the demo smoke test fails, the backend did not start correctly. That is the value of automation: it catches the problem before we merge or demo.
