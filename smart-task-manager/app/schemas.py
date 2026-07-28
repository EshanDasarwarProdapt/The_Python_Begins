"""
Pydantic schemas ("shapes" of data going in/out over the API).

Single responsibility of this file: define what valid JSON looks like
for creating, updating, and returning tasks. This is where request
validation happens (FastAPI runs these automatically) - if a client
sends bad data (e.g. priority="Urgent" instead of "High"), FastAPI
rejects it with a 422 error *before* our code ever runs.

Keeping this separate from models.py is a deliberate layering choice:
- models.py describes the DATABASE table.
- schemas.py describes the API's INPUT/OUTPUT JSON.
They often look similar but serve different purposes, and in bigger
apps they can diverge a lot (e.g. hiding internal fields from clients).
"""

from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

# Reusable "allowed values" types. Using Literal means Pydantic will
# reject anything that isn't exactly one of these strings.
Priority = Literal["Low", "Medium", "High"]
Status = Literal["Pending", "In Progress", "Completed"]


class TaskBase(BaseModel):
    """Fields shared by create/update - not used directly, just inherited."""

    title: str = Field(min_length=3, max_length=200)
    description: Optional[str] = None
    priority: Priority
    status: Status = "Pending"
    deadline: Optional[date] = None


class TaskCreate(TaskBase):
    """
    Body shape for `POST /tasks`.

    Note `created_at` and `id` are NOT here - the client never
    supplies them, the database generates them.
    """

    pass


class TaskUpdate(BaseModel):
    """
    Body shape for `PUT /tasks/{id}`.

    Every field is optional here because updates are "partial": a
    client might only want to change the `status`, for example, and
    leave everything else untouched. Our CRUD layer only updates
    fields that were actually provided.
    """

    title: Optional[str] = Field(default=None, min_length=3, max_length=200)
    description: Optional[str] = None
    priority: Optional[Priority] = None
    status: Optional[Status] = None
    deadline: Optional[date] = None


class TaskOut(TaskBase):
    """
    Response shape returned to clients - includes everything, including
    server-generated fields (`id`, `created_at`).
    """

    id: int
    created_at: datetime

    class Config:
        # Lets Pydantic build this schema directly from a SQLAlchemy
        # model instance (e.g. `TaskOut.model_validate(task_row)`)
        # instead of requiring a plain dict.
        from_attributes = True


class TaskStats(BaseModel):
    """Response shape for `GET /tasks/stats`."""

    total: int
    by_status: dict
    by_priority: dict
