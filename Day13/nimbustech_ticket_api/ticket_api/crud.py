"""
CRUD layer: the only place that talks directly to the database session.

Single responsibility of this file: take a SQLAlchemy `Session` plus
some plain Python arguments, and do the actual `db.add` / `db.query` /
`db.delete` / `db.commit` work.

WHY keep this separate from the routers (ticket_api/main.py)?
  1. Single Responsibility: a router's job is to handle HTTP concerns
     (status codes, path/query params). It shouldn't also contain
     database query logic - that's a different concern, and mixing
     them makes both harder to read.
  2. Testability: these functions take a plain `Session` and return
     plain Python/SQLAlchemy objects - no `Request`/`Response` objects
     involved. That means we can unit-test `create_ticket`, `get_ticket`,
     etc. directly, without spinning up a whole FastAPI app.
  3. Reuse: if we ever added a CLI tool or a background job that also
     needs to create/update tickets, it could import these same
     functions instead of duplicating query logic.
"""

import logging
from collections import Counter
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from ticket_api.orm import Ticket
from ticket_processor.config import PRIORITY_MAP

logger = logging.getLogger("ticket_api.crud")


def create_ticket(db: Session, ticket_data: dict) -> Ticket:
    """Insert a new ticket row and return it (with id filled in)."""
    ticket_data = ticket_data.copy()

    # Generate the human-readable ticket_id.
    ticket_data["ticket_id"] = _next_ticket_id(db)

    # Derive priority score from raw priority.
    priority = ticket_data.get("priority_raw", "low")
    ticket_data["priority_score"] = PRIORITY_MAP.get(priority, 0)

    # Serialise created_at to a datetime if it isn't already.
    created_at = ticket_data.get("created_at", datetime.now())
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at)
    ticket_data["created_at"] = created_at

    # Calculate SLA breach.
    sla_hours = ticket_data.get("sla_hours", 0)
    status = ticket_data.get("status", "")
    ticket_data["sla_breached"] = _is_breached(created_at, sla_hours, status)

    ticket = Ticket(**ticket_data)
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    logger.info("Created ticket ticket_id=%s", ticket.ticket_id)
    return ticket


def get_ticket(db: Session, ticket_id: str) -> Ticket | None:
    """Fetch a single ticket by its human-readable ticket_id."""
    return db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()


def get_all_tickets(db: Session) -> list[Ticket]:
    """Return every ticket in the database."""
    return db.query(Ticket).all()


def get_breached_tickets(db: Session) -> list[Ticket]:
    """Return only tickets currently marked as SLA-breached."""
    return db.query(Ticket).filter(Ticket.sla_breached == True).all()


def update_ticket(db: Session, ticket_id: str, changes: dict) -> Ticket | None:
    """
    Apply a partial update to an existing ticket: only fields the client
    actually sent are changed.  Returns None if the ticket does not exist.
    """
    ticket = get_ticket(db, ticket_id)
    if ticket is None:
        return None

    for field, value in changes.items():
        setattr(ticket, field, value)

    # Recalculate derived fields after the update.
    if "priority_raw" in changes:
        ticket.priority_score = PRIORITY_MAP.get(ticket.priority_raw, 0)
    ticket.sla_breached = _is_breached(
        ticket.created_at, ticket.sla_hours, ticket.status
    )

    db.commit()
    db.refresh(ticket)
    logger.info("Updated ticket ticket_id=%s fields=%s", ticket_id, list(changes.keys()))
    return ticket


def delete_ticket(db: Session, ticket_id: str) -> bool:
    """Delete a ticket by its ticket_id. Returns True if deleted, False if missing."""
    ticket = get_ticket(db, ticket_id)
    if ticket is None:
        return False
    db.delete(ticket)
    db.commit()
    logger.info("Deleted ticket ticket_id=%s", ticket_id)
    return True


def get_summary(db: Session) -> dict:
    """Build live summary counts for the dashboard."""
    tickets = get_all_tickets(db)
    return {
        "total_rows": len(tickets),
        "valid_tickets": len(tickets),
        "invalid_rows": 0,
        "breached_count": len(get_breached_tickets(db)),
        "by_category": dict(Counter(t.category for t in tickets)),
    }


def _next_ticket_id(db: Session) -> str:
    """Return the next sequential ticket identifier."""
    last = (
        db.query(Ticket.ticket_id)
        .filter(Ticket.ticket_id.like("T-%"))
        .order_by(Ticket.id.desc())
        .first()
    )
    if last is None:
        return "T-1001"
    number = int(last.ticket_id.split("-")[-1])
    return f"T-{number + 1}"


def _is_breached(created_at: datetime, sla_hours: float, status: str) -> bool:
    """Calculate whether a ticket's SLA deadline has passed."""
    return created_at + timedelta(hours=sla_hours) < datetime.now() and (
        status.lower() != "closed"
    )