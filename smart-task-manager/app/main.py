"""
Application entry point.

Single responsibility of this file: wire everything else together -
create the FastAPI app, configure logging/CORS, create the database
tables, seed a few demo rows, register our custom error handlers, and
include the task router. Run it with:

    uvicorn app.main:app --reload

then open http://127.0.0.1:8000/docs
"""

import logging
from contextlib import asynccontextmanager
from datetime import date

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import models
from app.database import SessionLocal, engine
from app.exceptions import TaskNotFoundException
from app.routers import tasks

# --- Logging -----------------------------------------------------------
# Basic setup so students can see what's happening in the terminal:
# every create/update/delete logs a line (see app/crud.py), and any
# unexpected server error gets logged with a full traceback (see the
# generic exception handler below) instead of silently disappearing.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("app.main")


def seed_demo_data():
    """
    Insert a few example tasks the FIRST time the app runs (i.e. only
    if the `tasks` table is currently empty). This makes it easy for
    students/instructors to see something in `GET /tasks` immediately,
    without having to POST data manually first.
    """
    db = SessionLocal()
    try:
        if db.query(models.Task).count() == 0:
            demo_tasks = [
                models.Task(
                    title="Set up development environment",
                    description="Install Python, create a virtual environment, install requirements.",
                    priority="High",
                    status="Completed",
                    deadline=date(2026, 1, 10),
                ),
                models.Task(
                    title="Build the Tasks API",
                    description="Implement CRUD endpoints using FastAPI and SQLAlchemy.",
                    priority="High",
                    status="In Progress",
                    deadline=date(2026, 8, 1),
                ),
                models.Task(
                    title="Write unit tests",
                    description="Add tests for the CRUD layer using pytest.",
                    priority="Medium",
                    status="Pending",
                    deadline=None,
                ),
            ]
            db.add_all(demo_tasks)
            db.commit()
            logger.info("Seeded database with %d demo tasks.", len(demo_tasks))
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI "lifespan" function: code before `yield` runs once at
    startup, code after `yield` runs once at shutdown. We use it to
    create the database tables (if they don't exist yet) and seed some
    demo data - this replaces the older `@app.on_event("startup")`
    style, which is now deprecated.
    """
    models.Base.metadata.create_all(bind=engine)
    seed_demo_data()
    logger.info("Smart Task Manager API is starting up.")
    yield
    logger.info("Smart Task Manager API is shutting down.")


app = FastAPI(
    title="Smart Task Manager API",
    description="A simple FastAPI + SQLAlchemy + SQLite task manager, built for teaching.",
    version="1.0.0",
    lifespan=lifespan,
)

# --- CORS ----------------------------------------------------------------
# The frontend for this project is served separately (e.g. via VS Code
# "Live Server" on port 5500/5501), which counts as a different
# "origin" from our API (127.0.0.1:8000). Browsers block cross-origin
# requests by default, so we explicitly allow the common Live Server
# ports here. In a REAL production app you would list only your actual
# frontend domain(s) - NOT "*" - to avoid letting any website call
# your API on a logged-in user's behalf.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:5501",
        "http://localhost:5501",
        "*",  # fallback for teaching convenience - restrict this in production!
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Custom exception handlers -------------------------------------------
@app.exception_handler(TaskNotFoundException)
async def task_not_found_handler(request: Request, exc: TaskNotFoundException):
    """
    Turns our domain-level TaskNotFoundException (raised in crud.py)
    into the exact 404 JSON shape the frontend expects:
        {"detail": "Task with id {id} not found"}
    """
    return JSONResponse(
        status_code=404,
        content={"detail": f"Task with id {exc.task_id} not found"},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """
    Catch-all safety net: if ANYTHING unexpected goes wrong (a bug, a
    database error, etc.), we don't want to leak a raw Python
    traceback to API clients. We log the real error server-side (so
    developers/instructors can debug it) and return a generic, safe
    500 response to the client instead.
    """
    logger.exception("Unhandled error while processing request: %s %s", request.method, request.url)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# --- Routers ---------------------------------------------------------------
app.include_router(tasks.router)


# --- Misc top-level routes --------------------------------------------------
@app.get("/health")
def health_check():
    """Simple endpoint to confirm the server is up - good first thing to test."""
    return {"status": "ok"}


@app.get("/")
def root():
    """Small welcome message pointing people at the interactive docs."""
    return {
        "message": "Welcome to the Smart Task Manager API.",
        "docs": "/docs",
    }
