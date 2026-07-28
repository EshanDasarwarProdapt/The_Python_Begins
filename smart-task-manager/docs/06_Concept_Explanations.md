# Concept Explanations
## What is it, why did we use it, and where does it live in this project?

This document is the reference to pull up whenever a student asks "wait, what does that actually mean?" Each concept is explained in plain language first, then tied to the exact file/line where it's used.

---

## 1. Modules and Packages

**What:** A *module* is just one Python file. A *package* is a folder of modules that Python recognizes as a unit (traditionally by containing an `__init__.py` file).

**Why:** One giant file becomes impossible to navigate as a project grows. Splitting by responsibility means you can open exactly the file you need and ignore the rest.

**Where:** The entire `app/` folder. `app/routers/` is a sub-package inside it. `import app.models`, `from app.database import get_db`, etc. are all module imports in action.

## 2. Scripting Best Practices

**What:** The habits that separate a "script that works on my machine" from code a team can maintain: clear names, constants instead of magic values, a requirements file, logging instead of scattered `print()`, docstrings.

**Why:** Six months from now (or six minutes from now, for a classmate), someone needs to understand this code without asking you.

**Where:** `requirements.txt` (reproducible installs), `app/utils.py` (constants like allowed priorities), `logging.basicConfig(...)` in `main.py` (structured logs instead of `print`), and the docstring at the top of every single file in this project.

## 3. FastAPI Introduction

**What:** FastAPI is a Python web framework — it turns Python functions into HTTP endpoints, and generates interactive documentation automatically.

**Why:** It's fast to write, has excellent built-in validation (via Pydantic), and the auto-generated `/docs` page means you can test your API before any frontend exists.

**Where:** `app = FastAPI(...)` in `main.py` — the single object everything else attaches to.

## 4. Advanced FastAPI

**What:** The features that go beyond a single `@app.get(...)`: `APIRouter` (grouping related routes into their own file), `Depends()` (Dependency Injection — see #13), response models (declaring the exact shape of what a route returns), status codes, and tags (grouping routes in the docs UI).

**Why:** Real APIs have dozens of routes. Without routers, `main.py` would become another giant file — the same problem Modules and Packages solves, one level up.

**Where:** `app/routers/tasks.py` (`APIRouter(prefix="/tasks", tags=["Tasks"])`), `response_model=TaskOut` on every route, `status_code=201`/`204` set explicitly where the default `200` isn't correct.

## 5. API Project

**What:** The discipline of designing a coherent set of endpoints around a resource (here, "tasks") rather than a grab-bag of unrelated functions.

**Why:** Consistent, predictable APIs are easier for any client (a frontend, a mobile app, another service) to use correctly.

**Where:** The full set — `POST /tasks`, `GET /tasks`, `GET /tasks/{id}`, `PUT /tasks/{id}`, `DELETE /tasks/{id}`, `GET /tasks/stats` — all in `app/routers/tasks.py`.

## 6. API Testing

**What:** Verifying an API actually behaves as documented, using tools instead of guessing: FastAPI's auto-generated Swagger UI at `/docs`, or an external tool like Postman.

**Why:** "It compiles" isn't the same as "it works." Testing the actual HTTP responses (status codes, JSON shape, error cases) catches real bugs.

**Where:** Every route in `app/routers/tasks.py` is testable at `http://127.0.0.1:8000/docs` the moment the server starts — no extra setup needed, because FastAPI builds this page from your code automatically.

## 7. JavaScript Essentials

**What:** The core building blocks of the language: variables (`let`/`const`), functions, objects (`{}`), arrays (`[]`), loops (`for`, `.map()`, `.forEach()`), reading/changing the page (DOM manipulation), and responding to user actions (event listeners).

**Why:** Every dynamic behavior in a webpage — showing data, responding to clicks, updating without reloading — is built from these fundamentals.

**Where:** `frontend/app.js` throughout: `document.getElementById(...)`, `.addEventListener("submit", ...)`, building task card HTML inside a loop over an array of task objects, reading form values into a plain JS object before sending it to the server.

## 8. Asynchronous JavaScript

**What:** JavaScript normally runs one line at a time, in order. But some operations — like asking a server for data over the network — take an unpredictable amount of time. `async`/`await` lets code *wait* for those operations to finish, without freezing everything else on the page while it waits.

**Plain-language analogy:** ordering food at a counter. You place your order (`fetch(...)`), you get a buzzer (a `Promise`), and you go sit down — you don't stand frozen at the counter. When the buzzer goes off (`await` resolves), you get your food (the data) and continue. Meanwhile, other people could still place their own orders (the browser stays responsive).

**Why:** Without this, calling the backend would either need clunky callback chains or would freeze the browser tab while waiting for a response. `async`/`await` makes asynchronous code *read* like normal, top-to-bottom code.

**Where:** Every function in `frontend/app.js` that talks to the backend is declared `async` and uses `await fetch(...)`: `fetchTasks()`, `createTask()`, `updateTask()`, `deleteTaskOnServer()`, `fetchStats()`. None of them use `.then()` chains — deliberately, so the code stays easy to read top-to-bottom.

## 9. NodeJS Essentials

**What:** Node.js is a JavaScript runtime that runs JavaScript *outside* the browser — on your own machine or a server. `npm` (Node Package Manager) installs and manages JavaScript libraries and tools; `npx` runs them without installing permanently; `package.json` describes a Node project's dependencies and scripts.

**Why (even though this backend is Python, not Node):** modern frontend development almost always involves Node-based tooling *somewhere* — even just to run a local development server, a linter, or a build tool. Understanding Node/npm means you're not confused the first time you see a `package.json` in a real job.

**Where:** VS Code's "Live Server" extension (used to serve `frontend/` on `localhost:5500`) is itself a small Node/npm-based tool running quietly in the background. If this project's frontend later grew into a React or Vite app, `npm install` / `npm run dev` is exactly the tooling that would take over — the architecture in the Design Document is deliberately compatible with that future upgrade.

## 10. API Fundamentals

**What:** The universal pattern underneath almost every web application: a **client** (the browser) sends an **HTTP request** (with a method like `GET`/`POST`/`PUT`/`DELETE`, a URL, and optionally a JSON body) to a **server**, which processes it and sends back an **HTTP response** (a status code + JSON body).

**Why:** Once you understand this pattern, you understand how *any* API works — not just this one.

**Where:** Traced end to end in the Design Document, Section 3 ("The Complete Request Flow"). Concretely: `frontend/app.js`'s `fetch()` calls are the client side; `app/routers/tasks.py` is the server side; the JSON going back and forth is defined by `app/schemas.py`.

## 11. Request Validation

**What:** Checking that incoming data meets the rules *before* acting on it — right length, right type, one of a fixed set of allowed values.

**Why:** Garbage input should never reach the database. Catching bad data at the door, automatically, is far safer than hoping every code path remembers to check manually.

**Where:** `app/schemas.py` — `TaskCreate.title: str = Field(min_length=3, max_length=200)`, `priority: Literal["Low", "Medium", "High"]`, `status: Literal["Pending", "In Progress", "Completed"]`. FastAPI runs this validation automatically before the route function ever executes; invalid requests get an automatic `422 Unprocessable Entity` response with details on exactly which field failed.

## 12. Exception Handling

**What:** Deciding, deliberately, what happens when something goes wrong — instead of letting the program crash or return something confusing.

**Why:** Real users (and real APIs) will eventually ask for a task that was already deleted, or send a request while the database is unavailable. A well-built system fails *predictably* and *informatively*.

**Where:** `app/exceptions.py` defines `TaskNotFoundException`. `app/main.py` registers two handlers: one that turns `TaskNotFoundException` into a clean `404` with a message like `"Task with id 57 not found"`, and a catch-all that turns *any* unexpected error into a safe generic `500` (while logging the real error server-side for debugging). On the frontend, `frontend/app.js` reads the `detail` message from failed responses and shows it in an on-screen error banner instead of a raw crash.

## 13. Database Integration

**What:** Connecting the application to persistent storage so data survives after the server restarts. SQLAlchemy is an ORM (Object-Relational Mapper) — it lets you work with the database using Python classes and objects (`Task`, `db.add()`, `db.query()`) instead of writing raw SQL strings by hand.

**Why:** See Design Document §4.1 for the full trade-off discussion (ORM vs. raw SQL) and §4.2 (SQLite vs. PostgreSQL). Short version: the ORM is safer (no manual SQL string-building), more Pythonic, and easy to swap the underlying database later without touching business logic.

**Where:** `app/database.py` (engine + session setup), `app/models.py` (the `Task` model = one row shape), `app/crud.py` (`db.add()`, `db.commit()`, `db.query()`, `db.delete()` — every actual database operation in the project lives here and nowhere else).

## 14. Dependency Injection (`Depends()`)

**What:** Instead of a function creating everything it needs itself, it *declares* what it needs, and the framework provides it.

**Why:** Every route needs a database session, but none of them should be responsible for creating and safely closing one — that's repetitive and error-prone. `Depends(get_db)` lets FastAPI handle that plumbing consistently, every time.

**Where:** `db: Session = Depends(get_db)` appears in every route in `app/routers/tasks.py`. `get_db()` itself lives in `app/database.py`.

## 15. VS Code Workflow (Tooling)

**What:** The practical, day-to-day mechanics of building this in an editor.

**Why:** Knowing the tool speeds up everything else.

**How, concretely:**
- Install the **Python** extension (for linting, run/debug, and virtual environment detection) and the **Live Server** extension (to serve the frontend with one right-click).
- Use the integrated terminal (`` Ctrl+` ``) for all commands: creating the venv, `pip install`, and running `uvicorn`.
- Right-click `frontend/index.html` → **Open with Live Server** to serve the frontend on `http://127.0.0.1:5500` with auto-reload on save.
- Use the built-in debugger (the "Run and Debug" panel, or pressing F5) to step through Python code line by line if something isn't behaving as expected — a much faster way to find bugs than adding `print()` everywhere.
