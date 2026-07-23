"""Pydantic models used by the ticket API."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ticket_processor.config import PRIORITY_MAP


class TicketCreate(BaseModel):
    """Validate the data accepted when creating a ticket."""

    customer_name: str = Field(min_length=1)
    category: str = Field(min_length=1)
    priority_raw: str
    sla_hours: float = Field(gt=0)
    status: str = Field(min_length=1)
    created_at: datetime = Field(default_factory=datetime.now)

    @field_validator("priority_raw")
    @classmethod
    def validate_priority(cls, value: str) -> str:
        """Normalise and validate a ticket priority."""
        priority = value.lower().strip()
        if priority not in PRIORITY_MAP:
            raise ValueError("priority must be low, medium, high, or critical")
        return priority


class TicketUpdate(BaseModel):
    """Validate the fields that can be changed on an existing ticket."""

    model_config = ConfigDict(extra="forbid")

    status: str | None = Field(default=None, min_length=1)
    priority_raw: str | None = None

    @field_validator("priority_raw")
    @classmethod
    def validate_priority(cls, value: str | None) -> str | None:
        """Normalise and validate an optional ticket priority."""
        if value is None:
            return None
        priority = value.lower().strip()
        if priority not in PRIORITY_MAP:
            raise ValueError("priority must be low, medium, high, or critical")
        return priority
