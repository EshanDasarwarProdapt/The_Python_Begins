"""
SQLAlchemy ORM models.

Single responsibility of this file: describe what a "Task" looks like
as a database TABLE (columns, types, defaults). This is the "M" in a
typical layered architecture - it knows nothing about HTTP, JSON, or
FastAPI. Validation of INCOMING data (e.g. "priority must be Low,
Medium or High") is deliberately handled in Pydantic schemas
(schemas.py), not here, to keep the database layer simple.
"""

from sqlalchemy import Column, Integer, String, Text, Date, DateTime
from sqlalchemy.sql import func

from app.database import Base


class Task(Base):
    """The `tasks` table: a single to-do item."""

    __tablename__ = "tasks"

    # Auto-incrementing primary key.
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)

    # Short title, required. Minimum length is enforced in the Pydantic
    # schema, not here - the database column itself just needs a type.
    title = Column(String(200), nullable=False)

    # Longer free-text description, optional.
    description = Column(Text, nullable=True)

    # We store priority/status as plain strings (not a DB-level enum)
    # to keep the SQL simple for students. The allowed values are
    # validated by Pydantic's `Literal[...]` types before they ever
    # reach the database - see schemas.py.
    priority = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, default="Pending")

    # Optional due date (date only, no time-of-day).
    deadline = Column(Date, nullable=True)

    # Set automatically by the DATABASE when a row is inserted
    # (server_default=func.now()) - the client can never set or
    # override this value.
    created_at = Column(DateTime(timezone=True), server_default=func.now())
