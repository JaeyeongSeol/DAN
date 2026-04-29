# DAN — Digital Offline Assistant for Notes
## ACIT 2911 Project — Team Roles & Weekly Plans

---

## Person 1 — AI Logic Lead / Product Owner
**Mateus**

> Own the AI feature direction and keep the MVP focused.

### Week 1
- Help finalize the project idea, MVP, and product name
- Write the problem and solution statement
- Define the AI features clearly: summarize notes and extract action items
- Help create user stories for the AI features
- Research/test the easiest local AI setup using Ollama/Gemma

### Week 2
- Create placeholder/mock AI functions so backend/frontend can develop without waiting for the model
- Write function signatures like `summarize_note(text)` and `extract_action_items(text)`
- Decide the expected AI output format
- Help backend know what data the AI functions return

### Week 3
- Connect the real local Gemma/Ollama model if possible
- Write and test prompts for summaries and action-item extraction
- Clean/parse AI output into usable data
- Build or support the user approval flow for AI-generated tasks

### Week 4
- Polish AI behavior for the final demo
- Prepare demo examples
- Explain the AI workflow in the presentation
- Make sure there is a fallback mode if local AI fails during demo

**Main Deliverable:** Working AI helper functions plus clear AI demo flow.

---

## Person 2 — Database & Data Access Lead
**Dan Shakya**

> Own the SQLite database and pure Python data access functions.

### Week 1
- Help decide what data the app needs to store
- Draft the database schema
- Tables should likely include: notes, tasks, and maybe AI suggestions
- Coordinate with backend lead so table fields match API needs

### Week 2
- Implement SQLite database setup
- Create notes table and tasks table
- Write CRUD functions for notes
- Write CRUD functions for tasks
- Make sure SQL queries are safe and parameterized
- Write basic tests for database functions

### Week 3
- Add support for AI-generated task suggestions if needed
- Help backend save approved AI-generated tasks
- Fix database bugs found during integration
- Improve tests

### Week 4
- Clean up database code
- Add seed/demo data if useful
- Help make sure final demo data is stable

**Main Deliverable:** A Python database module that backend can import and use.

---

## Person 3 — Backend API Lead
**Daniel McLean**

> Build the FastAPI backend that connects the frontend, database, and AI logic.

### Week 1
- Set up the FastAPI project structure
- Create initial health check route
- Agree on API route names with frontend/database/AI leads
- Help document the API plan

### Week 2
- Build notes API routes: create, read, update, delete
- Build tasks API routes: create, read, update, complete, delete
- Connect routes to database functions
- Add basic error handling and status codes

### Week 3
- Add AI routes like `/api/ai/summarize` and `/api/ai/extract-tasks`
- Connect AI routes to AI helper functions
- Connect approved AI-generated tasks to task creation
- Add backend tests with Pytest

### Week 4
- Fix integration bugs
- Clean API responses
- Help prepare backend demo flow
- Make sure tests pass before final presentation

**Main Deliverable:** A working FastAPI backend with CRUD and AI routes.

---

## Person 4 — Frontend UI Lead

> Build a clean React interface that makes the app feel polished and easy to demo.

### Week 1
- Create rough wireframes or layout ideas
- Set up React project if assigned
- Create placeholder screens for dashboard, notes, tasks, and AI assistant
- Coordinate with backend lead on expected API data

### Week 2
- Build notes list and note editor UI
- Build tasks list UI
- Connect frontend to notes/tasks API
- Add basic loading/error states

### Week 3
- Build AI assistant panel
- Add summarize button on notes
- Add extract action items button
- Build confirmation UI for AI-generated tasks before saving

### Week 4
- Polish styling and layout
- Make the demo flow smooth
- Fix responsive/UI issues
- Prepare clean screenshots for presentation if needed

**Main Deliverable:** A polished React frontend for notes, tasks, AI actions, and demo flow.

---

## Person 5 — Scrum Master / Integration, Testing & DevOps Lead
**Jaeyeong**

> Keep the team organized and make sure the project runs reliably.

### Week 1
- Set up or help set up GitHub repo
- Set up task manager: GitHub Projects, Trello, or Asana
- Help write Git workflow
- Track Team Charter and proposal responsibilities
- Run short standups/check-ins

### Week 2
- Help everyone follow feature-branch workflow
- Set up Pytest structure
- Start GitHub Actions if possible
- Help database/backend/frontend integrate their work
- Track blockers

### Week 3
- Finish GitHub Actions so tests run automatically
- Help test AI/backend/frontend integration
- Make sure setup instructions are clear
- Help create fallback plan for local AI model issues

### Week 4
- Make sure tests pass
- Help write final README/setup docs
- Coordinate final presentation materials
- Make sure everyone has a speaking part
- Help run through final demo

**Main Deliverable:** Organized Agile process, working CI/CD, clear setup docs, and stable final demo.
