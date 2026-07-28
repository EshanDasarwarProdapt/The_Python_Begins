# Task Breakdown
## Smart Task Manager — Ordered Build Tasks

This is the granular checklist behind the Teaching Guide (`05_Build_Sequence_Teaching_Guide.md`). Use it to track progress live in class, or as a student self-checklist. Tasks are grouped into phases in the order they should be built and taught.

---

## Phase 0 — Project Setup

| # | Task | File(s) | Topic Taught |
|---|---|---|---|
| 0.1 | Create the root project folder and empty subfolders (`app/`, `app/routers/`, `frontend/`) | folder structure | Modules and Packages |
| 0.2 | Create and activate a Python virtual environment | terminal | Scripting Best Practices |
| 0.3 | Create `requirements.txt` and install dependencies | `requirements.txt` | Scripting Best Practices |
| 0.4 | Open the project in VS Code, install the Python extension | VS Code | Tooling |

## Phase 1 — Database Layer

| # | Task | File(s) | Topic Taught |
|---|---|---|---|
| 1.1 | Configure the SQLite connection string and engine | `app/database.py` | Database Integration |
| 1.2 | Write the `get_db()` dependency generator | `app/database.py` | Advanced FastAPI (Dependency Injection) |
| 1.3 | Define the `Task` SQLAlchemy model (columns, types) | `app/models.py` | Database Integration |

## Phase 2 — Validation Layer

| # | Task | File(s) | Topic Taught |
|---|---|---|---|
| 2.1 | Define `TaskCreate` schema (required fields, allowed values) | `app/schemas.py` | Request Validation |
| 2.2 | Define `TaskUpdate` schema (all fields optional) | `app/schemas.py` | Request Validation |
| 2.3 | Define `TaskOut` response schema | `app/schemas.py` | Request Validation, API Project |

## Phase 3 — Business Logic Layer

| # | Task | File(s) | Topic Taught |
|---|---|---|---|
| 3.1 | Write `create_task()` | `app/crud.py` | Database Integration |
| 3.2 | Write `get_task()` / `get_tasks()` (with search/filter/sort) | `app/crud.py` | Database Integration, API Fundamentals |
| 3.3 | Write `update_task()` | `app/crud.py` | Database Integration |
| 3.4 | Write `delete_task()` | `app/crud.py` | Database Integration |
| 3.5 | Write `get_stats()` | `app/crud.py` | Database Integration |

## Phase 4 — Error Handling Layer

| # | Task | File(s) | Topic Taught |
|---|---|---|---|
| 4.1 | Define `TaskNotFoundException` | `app/exceptions.py` | Exception Handling |
| 4.2 | Register exception handlers (404, 500) | `app/main.py` | Exception Handling |
| 4.3 | Add logging for create/update/delete actions | `app/utils.py`, `app/main.py` | Scripting Best Practices |

## Phase 5 — API Layer

| # | Task | File(s) | Topic Taught |
|---|---|---|---|
| 5.1 | Create the `APIRouter` and wire up `POST /tasks` | `app/routers/tasks.py` | FastAPI Introduction, Advanced FastAPI |
| 5.2 | Wire up `GET /tasks` with query params (search/status/priority) | `app/routers/tasks.py` | API Fundamentals |
| 5.3 | Wire up `GET /tasks/stats` (registered before `/tasks/{id}`) | `app/routers/tasks.py` | Advanced FastAPI |
| 5.4 | Wire up `GET /tasks/{id}` | `app/routers/tasks.py` | API Fundamentals |
| 5.5 | Wire up `PUT /tasks/{id}` | `app/routers/tasks.py` | API Fundamentals |
| 5.6 | Wire up `DELETE /tasks/{id}` | `app/routers/tasks.py` | API Fundamentals |
| 5.7 | Create `main.py`, mount the router, add CORS middleware | `app/main.py` | FastAPI Introduction |
| 5.8 | Run the server and test everything in Swagger UI | `/docs` | API Testing |

## Phase 6 — Frontend Structure

| # | Task | File(s) | Topic Taught |
|---|---|---|---|
| 6.1 | Build the HTML skeleton: header, form, search bar, card container, stats panel | `frontend/index.html` | JavaScript Essentials (DOM structure) |
| 6.2 | Style the layout, form, cards, and badges | `frontend/style.css` | Frontend fundamentals |

## Phase 7 — Frontend Behavior

| # | Task | File(s) | Topic Taught |
|---|---|---|---|
| 7.1 | Define `API_BASE_URL` and write `fetchTasks()` | `frontend/app.js` | Asynchronous JavaScript |
| 7.2 | Render tasks as cards in the DOM | `frontend/app.js` | JavaScript Essentials (DOM, loops, arrays) |
| 7.3 | Wire up the Add/Edit form submit handler | `frontend/app.js` | JavaScript Essentials (events, objects) |
| 7.4 | Write `createTask()` / `updateTask()` (async, fetch POST/PUT) | `frontend/app.js` | Asynchronous JavaScript |
| 7.5 | Write `deleteTaskOnServer()` with confirmation | `frontend/app.js` | Asynchronous JavaScript |
| 7.6 | Wire up search input (debounced) and filter dropdowns | `frontend/app.js` | JavaScript Essentials, Asynchronous JavaScript |
| 7.7 | Write `fetchStats()` and render the stats panel | `frontend/app.js` | Asynchronous JavaScript |
| 7.8 | Add error banner handling for failed requests | `frontend/app.js` | Exception Handling (frontend side) |

## Phase 8 — Running & Testing End to End

| # | Task | Tool | Topic Taught |
|---|---|---|---|
| 8.1 | Start the backend with `uvicorn app.main:app --reload` | Terminal | FastAPI Introduction |
| 8.2 | Serve the frontend with VS Code Live Server | VS Code | NodeJS Essentials |
| 8.3 | Test each endpoint in Swagger UI first | `/docs` | API Testing |
| 8.4 | Test the same flows through the actual UI | Browser | End-to-end |
| 8.5 | Deliberately trigger errors (blank title, delete twice) to see graceful handling | Browser + `/docs` | Exception Handling |

## Phase 9 — Stretch Goals (If Time Allows)

| # | Task | Notes |
|---|---|---|
| 9.1 | Pagination (`limit`/`offset`) | Already supported in `GET /tasks` — just expose it in the UI. |
| 9.2 | Sort by deadline or created date | Already supported server-side (`sort_by`, `order`) — add a dropdown. |
| 9.3 | Soft delete (archive instead of remove) | Add an `archived` boolean column instead of a hard delete. |
| 9.4 | Postman collection for manual API testing | Export requests for each endpoint. |
