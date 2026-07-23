"""In-memory ticket storage backed by the processor report."""

import json
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

from ticket_processor.config import PRIORITY_MAP


PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORT_PATH = PROJECT_ROOT / "data" / "tickets_report.json"


class TicketStore:
    """Load, query, and mutate tickets for the lifetime of the API process."""

    def __init__(self, report_path: Path = REPORT_PATH) -> None:
        """Load the ticket report into memory."""
        if not report_path.exists():
            raise FileNotFoundError(
                f"Ticket report not found: {report_path}. Run the processor first."
            )

        with report_path.open(encoding="utf-8") as report_file:
            report = json.load(report_file)

        self.tickets: list[dict] = report.get("tickets", [])
        self.invalid_rows: list[dict] = report.get("invalid_rows", [])

    def get_all(self) -> list[dict]:
        """Return all tickets in the store."""
        return self.tickets

    def get_breached(self) -> list[dict]:
        """Return only tickets currently marked as SLA-breached."""
        return [ticket for ticket in self.tickets if ticket["sla_breached"]]

    def get_by_id(self, ticket_id: str) -> dict | None:
        """Find a ticket by its identifier."""
        return next(
            (ticket for ticket in self.tickets if ticket["ticket_id"] == ticket_id),
            None,
        )

    def create(self, ticket_data: dict) -> dict:
        """Create, store, and return a new ticket."""
        ticket_id = self._next_ticket_id()
        created_at = ticket_data["created_at"]
        created_text = created_at.isoformat()
        priority = ticket_data["priority_raw"]
        ticket = {
            "ticket_id": ticket_id,
            "customer_name": ticket_data["customer_name"],
            "category": ticket_data["category"],
            "priority_raw": priority,
            "priority_score": PRIORITY_MAP[priority],
            "created_at": created_text,
            "sla_hours": ticket_data["sla_hours"],
            "status": ticket_data["status"],
            "sla_breached": self._is_breached(
                created_at,
                ticket_data["sla_hours"],
                ticket_data["status"],
            ),
        }
        self.tickets.append(ticket)
        return ticket

    def update(self, ticket_id: str, changes: dict) -> dict | None:
        """Update an existing ticket's status and/or priority."""
        ticket = self.get_by_id(ticket_id)
        if ticket is None:
            return None

        ticket.update(changes)
        ticket["priority_score"] = PRIORITY_MAP[ticket["priority_raw"]]
        ticket["sla_breached"] = self._is_breached(
            datetime.fromisoformat(ticket["created_at"]),
            ticket["sla_hours"],
            ticket["status"],
        )
        return ticket

    def delete(self, ticket_id: str) -> bool:
        """Remove a ticket and indicate whether it existed."""
        ticket = self.get_by_id(ticket_id)
        if ticket is None:
            return False
        self.tickets.remove(ticket)
        return True

    def summary(self) -> dict:
        """Build live summary counts for the dashboard."""
        return {
            "total_rows": len(self.tickets) + len(self.invalid_rows),
            "valid_tickets": len(self.tickets),
            "invalid_rows": len(self.invalid_rows),
            "breached_count": len(self.get_breached()),
            "by_category": dict(Counter(ticket["category"] for ticket in self.tickets)),
        }

    def _next_ticket_id(self) -> str:
        """Return the next sequential ticket identifier."""
        numbers = [
            int(ticket["ticket_id"].split("-")[-1])
            for ticket in self.tickets
            if ticket["ticket_id"].startswith("T-")
            and ticket["ticket_id"].split("-")[-1].isdigit()
        ]
        return f"T-{max(numbers, default=1000) + 1}"

    @staticmethod
    def _is_breached(created_at: datetime, sla_hours: float, status: str) -> bool:
        """Calculate whether a ticket's SLA deadline has passed."""
        return created_at + timedelta(hours=sla_hours) < datetime.now() and (
            status.lower() != "closed"
        )
