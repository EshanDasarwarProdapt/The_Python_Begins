"""
SQLAlchemy ORM models for the NimbusTech Ticket API.

Single responsibility of this file: describe what a "Ticket" looks like
as a database TABLE (columns, types, defaults). This is the "M" in a
typical layered architecture - it knows nothing about HTTP, JSON, or
FastAPI. Validation of INCOMING data is deliberately handled in Pydantic
schemas (models.py), not here, to keep the database layer simple.
"""

from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.sql import func

from ticket_api.database import Base


class Ticket(Base):
    """The `tickets` table: a single support ticket."""

    __tablename__ = "tickets"

    # Auto-incrementing primary key.
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)

    # Human-readable ticket identifier like T-1001.
    ticket_id = Column(String(20), unique=True, nullable=False, index=True)

    # Customer who submitted the ticket.
    customer_name = Column(String(200), nullable=False)

    # Ticket category (e.g. Billing, Technical Support).
    category = Column(String(100), nullable=False)

    # Raw priority string (low, medium, high, critical).
    priority_raw = Column(String(20), nullable=False)

    # Numeric priority score derived from the raw priority.
    priority_score = Column(Integer, nullable=False)

    # Timestamp when the ticket was created.
    created_at = Column(DateTime, nullable=False, default=datetime.now)

    # SLA deadline in hours.
    sla_hours = Column(Float, nullable=False)

    # Current status of the ticket.
    status = Column(String(50), nullable=False)

    # Whether the SLA has been breached.
    sla_breached = Column(Boolean, nullable=False, default=False)

    def to_dict(self) -> dict:
        """Serialize the ORM instance to a plain dictionary for JSON responses."""
        return {
            "ticket_id": self.ticket_id,
            "customer_name": self.customer_name,
            "category": self.category,
            "priority_raw": self.priority_raw,
            "priority_score": self.priority_score,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "sla_hours": self.sla_hours,
            "status": self.status,
            "sla_breached": self.sla_breached,
        }
