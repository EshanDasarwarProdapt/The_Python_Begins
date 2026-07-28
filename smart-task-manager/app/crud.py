"""
CRUD layer: the only place that talks directly to the database session.

Single responsibility of this file: take a SQLAlchemy `Session` plus
some plain Python arguments, and do the actual `db.add` / `db.query` /
`db.delete` / `db.commit` work.

WHY keep this separate from the routers (app/routers/tasks.py)?
  1. Single Responsibility: a router's job is to handle HTTP concerns
     (status codes, path/query params). It shouldn't also contain
     database query logic - that's a different concern, and mixing
     them makes both harder to read.
  2. Testability: these functions take a plain `Session` and return
     plain Python/SQLAlchemy objects - no `Request`/`Response` objects
     involved. That means we can unit-test `create_task`, `get_task`,
     etc. directly, without spinning up a whole FastAPI app.
  3. Reuse: if we ever added a CLI tool or a background job that also
     needs to create/update tasks, it could import these same
     functions instead of duplicating query logic.
"""

import logging
from typing import Optional

from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

from app.exceptions import TaskNotFoundException
from app.models import Task
from app.schemas import TaskCreate, TaskUpdate
from app.utils import ALLOWED_PRIORITIES, ALLOWED_STATUSES, apply_search_filter

logger = logging.getLogger("app.crud")


def create_task(db: Session, task_in: TaskCreate) -> Task:
    """Insert a new task row and return it (with id/created_at filled in)."""
    task = Task(**task_in.model_dump())
    db.add(task)
    db.commit()
    # Refresh pulls back the auto-generated fields (id, created_at)
    # from the database into our Python object.
    db.refresh(task)
    logger.info("Created task id=%s title=%r", task.id, task.title)
    return task


def get_task(db: Session, task_id: int) -> Task:
    """
    Fetch a single task by id, or raise TaskNotFoundException if it
    doesn't exist. Centralizing the "not found" check here means every
    caller (get one, update, delete) behaves consistently.
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if task is None:
        raise TaskNotFoundException(task_id)
    return task


def get_tasks(
    db: Session,
    search: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    sort_by: str = "created_at",
    order: str = "desc",
    limit: int = 100,
    offset: int = 0,
):
    """
    Return a filtered, sorted, paginated list of tasks.

    Building the query step-by-step (start broad, then narrow it down
    with `.filter(...)` calls) is a common SQLAlchemy pattern - nothing
    actually hits the database until we call `.all()` at the end.
    """
    query = db.query(Task)

    if search:
        query = apply_search_filter(query, search)

    if status:
        query = query.filter(Task.status == status)

    if priority:
        query = query.filter(Task.priority == priority)

    # Only allow sorting by columns we expect - protects against typos
    # or unexpected input silently doing the wrong thing.
    sort_column = Task.deadline if sort_by == "deadline" else Task.created_at
    query = query.order_by(desc(sort_column) if order == "desc" else asc(sort_column))

    return query.offset(offset).limit(limit).all()


def update_task(db: Session, task_id: int, task_in: TaskUpdate) -> Task:
    """
    Apply a partial update to an existing task: only fields the client
    actually sent (`exclude_unset=True`) are changed.
    """
    task = get_task(db, task_id)  # raises TaskNotFoundException if missing

    updates = task_in.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)
    logger.info("Updated task id=%s fields=%s", task.id, list(updates.keys()))
    return task


def delete_task(db: Session, task_id: int) -> None:
    """Delete a task by id, raising TaskNotFoundException if missing."""
    task = get_task(db, task_id)  # raises TaskNotFoundException if missing
    db.delete(task)
    db.commit()
    logger.info("Deleted task id=%s", task_id)


def get_stats(db: Session) -> dict:
    """
    Build the aggregate counts used by `GET /tasks/stats`.

    For a teaching project we keep this simple and readable (loop +
    `.count()` per bucket) rather than reaching for a single fancy SQL
    GROUP BY query - it's easy for students to follow line by line.
    """
    total = db.query(Task).count()

    by_status = {
        status_value: db.query(Task).filter(Task.status == status_value).count()
        for status_value in ALLOWED_STATUSES
    }

    by_priority = {
        priority_value: db.query(Task).filter(Task.priority == priority_value).count()
        for priority_value in ALLOWED_PRIORITIES
    }

    return {"total": total, "by_status": by_status, "by_priority": by_priority}
