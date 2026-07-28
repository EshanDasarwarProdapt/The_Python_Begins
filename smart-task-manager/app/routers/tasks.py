"""
Task endpoints (the "Tasks" API).

Single responsibility of this file: define the HTTP routes for
creating/reading/updating/deleting tasks, and translate between
HTTP concepts (query params, status codes) and our CRUD layer
(app/crud.py). Notice the routes themselves contain almost no logic -
they just call a `crud.*` function and return its result. All the
actual database work lives in crud.py; this keeps each layer focused
on one job.
"""

from typing import Literal, Optional

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.schemas import TaskCreate, TaskOut, TaskStats, TaskUpdate

# `prefix="/tasks"` means every path below is automatically prefixed
# with /tasks (e.g. the create route below is really POST /tasks).
# `tags=["Tasks"]` just groups these nicely in the /docs UI.
router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.post("", response_model=TaskOut, status_code=201)
def create_task(task_in: TaskCreate, db: Session = Depends(get_db)):
    """
    Create a new task.

    `db: Session = Depends(get_db)` is FastAPI's Dependency Injection
    in action: FastAPI calls `get_db()` (see database.py) before this
    function runs, hands us a fresh database session, and closes it
    afterwards automatically. We never construct a session ourselves.
    """
    return crud.create_task(db, task_in)


@router.get("/stats", response_model=TaskStats)
def get_stats(db: Session = Depends(get_db)):
    """
    Aggregate counts of tasks by status/priority.

    IMPORTANT: this route is declared BEFORE `GET /tasks/{task_id}`
    below. FastAPI matches routes in the order they're registered, so
    if `/tasks/{task_id}` came first, a request to `/tasks/stats` would
    incorrectly match it (treating "stats" as an id) and fail.
    """
    return crud.get_stats(db)


@router.get("", response_model=list[TaskOut])
def list_tasks(
    search: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    sort_by: Literal["deadline", "created_at"] = "created_at",
    order: Literal["asc", "desc"] = "desc",
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """
    List tasks, with optional search/filter/sort/pagination via query
    params, e.g. GET /tasks?status=Pending&sort_by=deadline&order=asc
    """
    return crud.get_tasks(
        db,
        search=search,
        status=status,
        priority=priority,
        sort_by=sort_by,
        order=order,
        limit=limit,
        offset=offset,
    )


@router.get("/{task_id}", response_model=TaskOut)
def get_task(task_id: int, db: Session = Depends(get_db)):
    """
    Get a single task by id.

    If it doesn't exist, `crud.get_task` raises TaskNotFoundException,
    which main.py's exception handler turns into a clean 404 JSON
    response - the route itself doesn't need any error-handling code.
    """
    return crud.get_task(db, task_id)


@router.put("/{task_id}", response_model=TaskOut)
def update_task(task_id: int, task_in: TaskUpdate, db: Session = Depends(get_db)):
    """
    Partially update a task. Only fields present in the request body
    are changed (see TaskUpdate/crud.update_task for details).
    """
    return crud.update_task(db, task_id, task_in)


@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    """
    Delete a task. Returns 204 No Content (an empty body) on success,
    which is the conventional HTTP status code for "delete worked,
    there's nothing to send back".
    """
    crud.delete_task(db, task_id)
    return Response(status_code=204)
