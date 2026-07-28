# Build Sequence — Teaching Guide
## Smart Task Manager — "Let's build this, one step at a time"

This is the master script for teaching the project live. Follow it top to bottom, in order — each step says exactly what to build, in which file, why it comes at this point, and what to show students once it works. A finished, working reference copy of every file already exists in this project; use this guide to rebuild it live in front of students, narrating each decision.

Rough pacing: this comfortably spans 6–8 class sessions. Suggested session breaks are marked with 🔵.

---

## 🔵 Session 1 — Project Setup ("Let's create the skeleton first")

**Step s:** "Before we write a single line of logic, we set up the shape of the project. This is what 'Modules and Packages' means in practice — instead of one 2,000-line file, we split responsibilities into files that each do one job."

1. Create the root folder `smart-task-manager/`.
2. Inside it, create `app/` and, inside that, `routers/`. Create empty files: `main.py`, `database.py`, `models.py`, `schemas.py`, `crud.py`, `exceptions.py`, `utils.py`, and `routers/tasks.py`. Add empty `__init__.py` files to `app/` and `app/routers/` — this is literally what makes a folder a Python *package* rather than just a folder. Point this out explicitly.
3. Open the folder in VS Code. Install the **Python** extension if not already installed.
4. Open a terminal in VS Code (`` Ctrl+` ``) and create a virtual environment:
   ```
   python3 -m venv .venv
   ```
   Activate it (`.venv\Scripts\activate` on Windows, `source .venv/bin/activate` on Mac/Linux). Explain: a virtual environment keeps this project's Python packages separate from every other project on the machine.
5. Create `requirements.txt`:
   ```
   fastapi
   uvicorn[standard]
   sqlalchemy
   pydantic
   ```
   Run `pip install -r requirements.txt`. Explain: this file is how any teammate (or your future self) can recreate the exact same environment with one command — this is "Scripting Best Practices" in action.

**Checkpoint:** folder structure exists, venv is active, packages installed. Nothing runs yet — that's expected.

---

## 🔵 Session 2 — The Database Layer ("Let's connect the database first")

**Step :** "We always build from the bottom up: database → validation → business logic → API → frontend. If the foundation is solid, everything on top of it is easier."

1. **`app/database.py`** — set up the SQLAlchemy engine pointing at a local SQLite file, the `SessionLocal` factory, the `Base` class, and the `get_db()` dependency generator.
   - Explain **why SQLite**: zero setup, one file, perfect for learning (see Design Document §4.2 for the full trade-off vs. PostgreSQL).
   - Explain **why a generator with `yield`**: it guarantees the database connection is closed after every request, even if something goes wrong — write the `try / yield / finally` and narrate it line by line.
2. **`app/models.py`** — define the `Task` class inheriting from `Base`, with columns: `id`, `title`, `description`, `priority`, `status`, `deadline`, `created_at`.
   - Explain **ORM vs raw SQL** here (Design Document §4.1): "We're describing a database table using a normal-looking Python class. SQLAlchemy turns this into the actual `CREATE TABLE` SQL for us."

**Checkpoint:** run a tiny throwaway script that imports `Base.metadata.create_all()` and confirms `tasks.db` is created. Delete the throwaway script afterward (this gets built properly into `main.py` in Session 5).

---

## 🔵 Session 3 — The Validation Layer ("Let's define what valid data looks like")

**Step :** "Before we let any data anywhere near the database, we decide the rules for what 'valid' means. This is Request Validation."

1. **`app/schemas.py`** — build three Pydantic models:
   - `TaskCreate`: `title` (required, `min_length=3`), `description` (optional), `priority` (`Literal["Low","Medium","High"]`), `status` (defaults to `"Pending"`), `deadline` (optional date).
   - `TaskUpdate`: the same fields, but **all optional** — explain why: an edit might only change one field, so nothing should be required.
   - `TaskOut`: the shape returned to the client, including `id` and `created_at` (fields the client never sends, only receives).
   - Mention `TaskStats` too, for the statistics endpoint's response shape.
2. Show students: if you try to create a `TaskCreate` with `priority="Urgent"` (not an allowed value), Pydantic rejects it immediately — no code needed to check that manually.

**Checkpoint:** open a Python shell, import `TaskCreate`, construct one with bad data, watch it raise a `ValidationError` with a readable message.

---

## 🔵 Session 4 — The Business Logic Layer ("Let's teach the app how to actually do things")

**Step :** "Routes should be thin. All the real work — talking to the database — happens in one place: `crud.py`. That way, if we ever want to test our logic without running a whole web server, we can call these functions directly."

1. **`app/utils.py`** — small constants (`ALLOWED_PRIORITIES`, `ALLOWED_STATUSES`) and the logging setup helper.
2. **`app/exceptions.py`** — define `TaskNotFoundException`, a small class carrying the missing `task_id`.
3. **`app/crud.py`** — write, one at a time, narrating each:
   - `create_task(db, task_in)` → builds a `Task`, `db.add()`, `db.commit()`, `db.refresh()`, returns it.
   - `get_task(db, task_id)` → `db.query(Task).filter(...).first()`; if `None`, `raise TaskNotFoundException(task_id)`.
   - `get_tasks(db, search, status, priority, sort_by, order, limit, offset)` → builds up a query with `.filter()` calls added conditionally.
   - `update_task(db, task_id, task_in)` → fetch the task (reusing `get_task`), then only overwrite fields that were actually provided.
   - `delete_task(db, task_id)` → fetch, then `db.delete()`, `db.commit()`.
   - `get_stats(db)` → a few `db.query(Task).filter(...).count()` calls, one per status/priority.

**Checkpoint:** none yet visible in a browser — that's fine, tell students "we're building the engine before the car."

---

## 🔵 Session 5 — The API Layer ("Let's expose this to the world")

**Step :** "Now we turn our Python functions into an actual web API that anything — a browser, a phone app, another server — could talk to over HTTP. This is where FastAPI itself comes in."

1. **`app/routers/tasks.py`** — create `router = APIRouter(prefix="/tasks", tags=["Tasks"])`, then add, in this exact order (order matters!):
   - `POST ""` → create.
   - `GET "/stats"` → **must come before** `GET "/{task_id}"`, or FastAPI will think "stats" is an id. Point this out as a real, common beginner bug.
   - `GET ""` → list, with query parameters for search/filter/sort/pagination.
   - `GET "/{task_id}"` → get one.
   - `PUT "/{task_id}"` → update.
   - `DELETE "/{task_id}"` → delete, returning `204`.
   - Each route: show how little code is in it — it just calls the matching `crud.*` function.
   - Point out `Depends(get_db)` in every route signature — this is Dependency Injection, and it's the same pattern from Session 2.
   - Point out `response_model=TaskOut` — FastAPI uses this to both validate what we return AND generate the Swagger docs automatically.
2. **`app/main.py`** — this is the "front door":
   - `app = FastAPI(title=..., lifespan=lifespan)`.
   - A `lifespan` function that creates tables and seeds a few demo tasks on first run.
   - `CORSMiddleware`, explained as: "the frontend will run on a different port than the backend — browsers block that by default unless we explicitly allow it here."
   - The two `@app.exception_handler(...)` functions — one for our custom `TaskNotFoundException` → 404, one generic catch-all → 500 (never leak a raw Python error to a client).
   - `app.include_router(tasks.router)`.
   - A `/health` and `/` route.

**Checkpoint — the big one:** run `uvicorn app.main:app --reload`, open `http://127.0.0.1:8000/docs`, and let students **click Try it out** on every endpoint live. This is "API Testing." Deliberately try `GET /tasks/99999` to show the clean 404, and try `POST /tasks` with a blank title to show the automatic 422 validation error.

---

## 🔵 Session 6 — The Frontend Structure ("Let's give it a face")

**Step :** "Everything so far works, but only through Swagger. Real users need a webpage."

1. **`frontend/index.html`** — build, section by section: header, the add/edit task form (title/description/priority/status/deadline/save button), the search bar + priority/status dropdowns, an empty container `<div id="taskList">` where cards will be injected by JavaScript, and a stats panel with placeholders.
2. **`frontend/style.css`** — style the container, form, cards (with shadow + rounded corners), and colored priority/status badges. Keep it plain CSS — no framework — so nothing is hidden from students.
3. Open `index.html` directly in a browser (double-click, or right-click → "Open with Live Server" in VS Code) — it will look complete but do nothing yet (no JavaScript wired up).

**Checkpoint:** the page renders and looks like a real app, but clicking Save does nothing yet.

---

## 🔵 Session 7 — Asynchronous JavaScript ("Let's connect the frontend to the backend")

**Step :** "This is the payoff moment — where JavaScript Essentials and Asynchronous JavaScript come together to make this a real, dynamic, full-stack application."

1. At the top of **`frontend/app.js`**, define `const API_BASE_URL = "http://127.0.0.1:8000";` — point out: "This one line is the entire bridge between frontend and backend."
2. Write `fetchTasks()`:
   ```javascript
   async function fetchTasks() {
     const response = await fetch(`${API_BASE_URL}/tasks`);
     const tasks = await response.json();
     renderTasks(tasks);
   }
   ```
   Explain **`async`/`await`** with the "ordering food" analogy (see Concept Explanations doc) — the browser doesn't freeze while waiting for the server; other things can still happen.
3. Write `renderTasks(tasks)` — loop over the array, build a card's HTML for each task, inject it into `#taskList`. This is DOM manipulation.
4. Wire the form's `submit` event listener → build a plain JS object from the form fields → call `createTask()` or `updateTask()` depending on whether we're editing → `await fetch(..., {method: "POST"/"PUT", body: JSON.stringify(...)})`.
5. Wire each card's Edit button → pre-fill the form and remember the task's id. Wire Delete → `confirm()` then `await fetch(..., {method: "DELETE"})`.
6. Wire the search box (debounced) and the filter dropdowns → re-call `fetchTasks()` with query parameters appended to the URL.
7. Write `fetchStats()` → call it after every create/update/delete so the numbers stay live.

**Checkpoint — the moment it "clicks":** add a task through the UI and watch it appear instantly with **no page reload**. Open the browser's Network tab and show the actual `POST /tasks` request/response. This single demo is the entire "Complete Request Flow" from the Design Document, happening live.

---

## 🔵 Session 8 — NodeJS Essentials, Full Run-Through, and Wrap-Up

**Step :** "We didn't write any Node.js code directly in this project's backend — but Node is exactly what's running quietly under the hood of tools we *did* use."

1. Explain: VS Code's "Live Server" extension (used to serve `frontend/`) is itself a small Node.js/npm-based tool. Show `npx --version` / `npm --version` in the terminal to prove Node is installed. Briefly explain `package.json`, `npm install`, and `npx` conceptually, and mention that if this project's frontend later grew into something built with React or Vite, Node/npm is exactly what would run that build step.
2. Do one full, uninterrupted run-through with the class: start the backend (`uvicorn`), start the frontend (Live Server), and perform every feature end to end: add, search, filter, edit, delete, watch stats update.
3. Deliberately break things to show graceful failure: stop the backend server and try to add a task from the UI (show the error banner instead of a silent failure); try to load a deleted task's id directly.
4. Close with the "Where This Project Goes Next" section of the Design Document — authentication, deployment, Docker, PostgreSQL — so students see this as a foundation, not a finished ceiling.

---

## Quick Reference: Commands Used Throughout

```
# One-time setup
python3 -m venv .venv
source .venv/bin/activate        # or .venv\Scripts\activate on Windows
pip install -r requirements.txt

# Every time you work on the project
uvicorn app.main:app --reload    # starts the backend at http://127.0.0.1:8000
# then in VS Code: right-click frontend/index.html -> "Open with Live Server"
```
