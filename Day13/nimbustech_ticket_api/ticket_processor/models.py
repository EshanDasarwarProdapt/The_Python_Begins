from dataclasses import dataclass


@dataclass
class Ticket:
    """
    Represents a validated support ticket.

    Parameters:
        ticket_id: Unique ticket identifier.
        customer_name: Name of the customer.
        category: Ticket category.
        priority_raw: Original priority value from CSV.
        priority_score: Numeric priority score.
        created_at: Ticket creation timestamp.
        sla_hours: Allowed SLA duration in hours.
        status: Current ticket status.
        sla_breached: Whether the ticket breached its SLA.
    """

    ticket_id: str
    customer_name: str
    category: str
    priority_raw: str
    priority_score: int
    created_at: str
    sla_hours: float
    status: str
    sla_breached: bool


@dataclass
class InvalidRow:
    """
    Represents an invalid CSV row.

    Parameters:
        raw_row: Original CSV row data.
        reason: Reason why validation failed.
    """

    raw_row: dict
    reason: str
