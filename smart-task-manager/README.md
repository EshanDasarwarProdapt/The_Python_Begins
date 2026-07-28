# Smart Task Manager

A full-stack task management app (FastAPI + SQLAlchemy + SQLite backend,
plain HTML/CSS/JavaScript frontend), built as a teaching capstone for a
Python Full Stack course. It demonstrates routers, dependency injection,
Pydantic validation, custom exception handling, a layered architecture
(routes -> CRUD -> database), and an async-JavaScript frontend that talks
to it live.

## Start here: the docs

Read these in order - they explain *what* to build, *why*, and *how to
teach it* step by step:

1. `docs/01_PRD.md` (also available as a formatted `docs/Smart_Task_Manager_PRD.pdf`) - what this project is and why it exists.
2. `docs/02_Design_Document.md` - the architecture and every key design trade-off (ORM vs. raw SQL, SQLite vs. Postgres, REST vs. GraphQL, etc.), explained in plain language.
3. `docs/03_Core_Requirements.md` - the exact functional/non-functional requirements and tech stack.
4. `docs/04_Task_Breakdown.md` - the granular, ordered build checklist.
5. `docs/05_Build_Sequence_Teaching_Guide.md` - **the main one to teach from.** A session-by-session script: "build this file first, then this, then this," with the reasoning at each step.
6. `docs/06_Concept_Explanations.md` - a glossary/reference: what each concept is, why it's used, and exactly where it lives in the code (async JavaScript, Node.js, dependency injection, ORM, and everything else).

## Backend

## Quick start

1. **Create and activate a virtual environment** (from inside this folder):

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate        # on Windows: .venv\Scripts\activate
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Run the server:**

   ```bash
   uvicorn app.main:app --reload
   ```

4. **Open the interactive docs** in your browser:

   http://127.0.0.1:8000/docs

   From there you can try every endpoint (create, list, update, delete tasks)
   directly in the browser. A SQLite file `tasks.db` will be created
   automatically next to the `app/` folder the first time you run the
   server, pre-loaded with a few demo tasks.

## Where to look in the code

- `app/main.py` - creates the app, wires everything together.
- `app/database.py` - database connection + the `get_db` dependency.
- `app/models.py` - the `Task` database table.
- `app/schemas.py` - the request/response JSON shapes (Pydantic).
- `app/crud.py` - the actual database operations.
- `app/routers/tasks.py` - the `/tasks` HTTP endpoints.
- `app/exceptions.py` - our custom "task not found" error.
- `app/utils.py` - small shared constants/helpers.

## Frontend

The frontend for this project is built separately and served on its own
port (e.g. VS Code "Live Server" on `http://127.0.0.1:5500`). CORS is
already configured in `app/main.py` to allow that.
