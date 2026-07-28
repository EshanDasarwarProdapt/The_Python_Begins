# Design Document
## Smart Task Manager

This document explains **how** the project is built and **why** each decision was made. It's written for the instructor to read once, and to lean on whenever a student asks "but why did we do it this way instead of that way?"

---

## 1. Architecture Overview

```
   Browser (index.html + style.css + app.js)
              │
              │  fetch() over HTTP (JSON)
              ▼
   FastAPI Backend  (app/main.py + routers/tasks.py)
              │
              │  Python function calls
              ▼
   CRUD Layer  (app/crud.py)
              │
              │  SQLAlchemy ORM
              ▼
   SQLite Database  (tasks.db file)
```

Three layers, three responsibilities:

- **Frontend** — everything the user sees and clicks. Knows nothing about databases.
- **Backend (API)** — receives requests, validates them, decides what's allowed, talks to the database. Knows nothing about how the browser draws things.
- **Database** — stores the data permanently. Knows nothing about HTTP or JavaScript.

This separation is called a **layered architecture**, and it's the same pattern used by real production systems. Each layer can be changed without rewriting the others — for example, the frontend could later be rebuilt in React without touching a single line of Python.

## 2. File-by-File Responsibility

| File | Responsibility |
|---|---|
| `app/main.py` | Creates the FastAPI app, wires up CORS, registers routers, registers error handlers, seeds demo data. The "front door" of the backend. |
| `app/database.py` | Configures the SQLite connection and the `get_db()` dependency that hands out (and safely closes) database sessions. |
| `app/models.py` | The SQLAlchemy `Task` model — describes the database table in Python classes instead of raw SQL. |
| `app/schemas.py` | Pydantic models describing what valid input/output JSON looks like (`TaskCreate`, `TaskUpdate`, `TaskOut`). |
| `app/crud.py` | The only place that talks to the database directly (`db.add`, `db.query`, `db.commit`, `db.delete`). Routers never touch the database themselves. |
| `app/exceptions.py` | Custom exceptions like "task not found," so errors have meaning instead of being generic crashes. |
| `app/utils.py` | Small shared constants and helpers (allowed priority/status values, logging setup). |
| `app/routers/tasks.py` | The actual API endpoints (`/tasks`, `/tasks/{id}`, `/tasks/stats`). Thin — each endpoint just validates input, calls a `crud.py` function, and returns the result. |
| `frontend/index.html` | The page structure: the form, the search bar, the card container, the stats panel. |
| `frontend/style.css` | All visual styling — colors, spacing, card layout, badges. |
| `frontend/app.js` | All frontend behavior — fetching data, rendering cards, handling clicks, calling the API asynchronously. |

## 3. The Complete Request Flow (Traced)

Walking through what happens when a user clicks **Save** on a new task, end to end:

1. User fills the form and clicks **Save**.
2. `app.js`'s form submit handler runs, builds a plain JavaScript object from the form fields.
3. An `async function` calls `await fetch(API_BASE_URL + "/tasks", { method: "POST", body: JSON.stringify(taskObject) })`.
4. The browser sends an HTTP `POST` request with a JSON body to `http://127.0.0.1:8000/tasks`.
5. FastAPI receives it and matches it to the route in `routers/tasks.py`.
6. FastAPI automatically parses the JSON body into the `TaskCreate` Pydantic schema. If anything is invalid (blank title, bad priority value), FastAPI **stops here** and sends back a `422` error automatically — the route function never even runs.
7. If validation passes, the route function calls `crud.create_task(db, task_data)`.
8. `crud.py` creates a `Task` SQLAlchemy object, calls `db.add(task)` and `db.commit()`.
9. SQLAlchemy translates that into real SQL and writes a new row into `tasks.db`.
10. `crud.py` returns the saved task (now including its new `id` and `created_at`).
11. The router returns it; FastAPI serializes it to JSON using the `TaskOut` response model and sends back `201 Created`.
12. Back in `app.js`, `await fetch(...)` resolves with the response. The code reads the JSON body, adds the new task to the on-screen list, and refreshes the statistics — **without reloading the page**.

This single click demonstrates almost every topic in the course.

## 4. Key Design Decisions & Trade-offs

Every non-trivial choice below is deliberately explained simply, with the honest trade-off — the goal is for students to understand *why*, not just copy the code.

### 4.1 SQLAlchemy ORM vs. raw SQL

**Chosen: SQLAlchemy ORM.**

- With raw SQL, you'd write `"INSERT INTO tasks (title, ...) VALUES (?, ?, ...)"` strings by hand — this works, but it's easy to make typos, easy to open yourself up to SQL injection if you build strings carelessly, and it doesn't feel like normal Python.
- With the ORM, you write `db.add(Task(title="..."))` — plain Python objects. SQLAlchemy generates the SQL for you.
- **Trade-off:** the ORM adds a learning curve (sessions, models, relationships) and a small performance overhead compared to hand-tuned raw SQL. For a small app like this, that overhead is irrelevant. In large, performance-critical systems, teams sometimes drop to raw SQL for specific hot-path queries — but they still use an ORM everywhere else because it's faster to write and safer by default. This is exactly why almost every production Python backend (Instagram, Reddit, countless internal tools) uses an ORM like SQLAlchemy or Django's ORM as the default, and only reaches for raw SQL when truly necessary.

### 4.2 SQLite vs. PostgreSQL/MySQL

**Chosen: SQLite.**

- SQLite stores the entire database as a single file (`tasks.db`) — zero setup, nothing to install or run separately. Perfect for learning and for small local apps.
- **Trade-off:** SQLite doesn't handle many simultaneous users writing at once as well as PostgreSQL/MySQL do, and it doesn't run as a separate server, so it isn't what you'd choose for a real multi-user production app. Because SQLAlchemy is used as the layer in between, switching to PostgreSQL later is mostly a one-line configuration change (`database.py`) — the rest of the code (`models.py`, `crud.py`, routers) doesn't need to change. That's the whole point of using an ORM.

### 4.3 REST (this project) vs. GraphQL

**Chosen: REST.**

- REST maps naturally to HTTP verbs (`GET`, `POST`, `PUT`, `DELETE`) and is far more common in junior/mid-level jobs and easier to learn first.
- **Trade-off:** REST can lead to over-fetching or under-fetching data in complex apps (GraphQL solves this by letting the client ask for exactly the fields it wants). For a project this size, that problem doesn't exist, so REST is the simpler, more teachable choice.

### 4.4 Separate frontend/backend servers vs. one combined server

**Chosen: two separate local servers** (backend on port 8000 via `uvicorn`, frontend on port 5500 via VS Code Live Server), connected via CORS.

- This mirrors how real teams work — a frontend team and a backend team, talking over an API contract — even though here it's the same person wearing both hats.
- **Trade-off:** this introduces CORS (Cross-Origin Resource Sharing), a browser security feature that blocks a webpage from calling an API on a different origin/port unless the API explicitly allows it. This is exactly why `main.py` includes `CORSMiddleware`. It's a bit of extra configuration, but it's a real-world concept every web developer eventually has to understand, so it's better to meet it here, in a safe learning environment, with a clear explanation, than to be confused by it for the first time on the job.

### 4.5 Vanilla JavaScript vs. a frontend framework (React/Vue)

**Chosen: plain HTML/CSS/JavaScript, no framework, no build step.**

- The course is teaching JavaScript Essentials and Asynchronous JavaScript as *fundamentals* — frameworks hide a lot of what's actually happening (the DOM updates, the fetch calls) behind abstractions. Learning the raw version first makes frameworks make sense later, instead of feeling like magic.
- **Trade-off:** vanilla JS means more manual DOM manipulation code than React would need. For an app this size, that's a small, manageable amount of code — and it's exactly the code that teaches the concepts.

### 4.6 Pydantic validation vs. manual `if` checks

**Chosen: Pydantic schemas.**

- Instead of writing `if not title: raise Error(...)` for every field by hand, Pydantic schemas declare the rules once (`min_length=3`, `Literal["Low","Medium","High"]`) and FastAPI enforces them automatically on every request.
- **Trade-off:** there's a small amount of new syntax to learn (schema classes, `Literal` types). In exchange, validation is consistent everywhere, self-documenting (it even shows up automatically in the `/docs` Swagger page), and impossible to accidentally skip.

### 4.7 Custom exception handling vs. letting errors crash

**Chosen: custom exceptions with dedicated handlers.**

- Without this, a request for a task that doesn't exist would either return a confusing generic error or crash the server process.
- With `TaskNotFoundException` and a registered handler in `main.py`, the same situation returns a clean `404` with a human-readable message (`"Task with id 57 not found"}`).
- **Trade-off:** it's a bit more code up front (defining exception classes, registering handlers), but it's what separates a "student script" from a "production-style API" — production systems are graded on how gracefully they fail, not just whether they work when everything goes right.

## 5. Security Notes (What's In and Out of Scope)

- Input validation (via Pydantic) protects against malformed data — this is included.
- There is **no authentication/authorization** in this version — anyone who can reach the API can do anything. This is intentional and called out explicitly: adding JWT-based login is a natural next module, not an oversight.
- CORS is configured for local development ports only, with a comment in the code explaining that production systems restrict this to their real frontend domain.

## 6. Where This Project Goes Next

Once the core app is built and understood, natural next steps (for a future course module, not this one) are: user accounts and JWT authentication, deployment to a cloud provider, containerizing with Docker, and moving from SQLite to PostgreSQL for multi-user use. The architecture in this document was chosen specifically so that each of those additions is possible without a rewrite.
