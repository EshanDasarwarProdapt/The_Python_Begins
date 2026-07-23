"""
Core processing functions for NimbusTech ticket processing.
"""

import csv
import json
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

from ticket_processor.config import (
    DATE_FORMAT,
    INVALID_ROW_ABORT_RATIO,
    PRIORITY_MAP,
)
from ticket_processor.models import InvalidRow, Ticket
from ticket_processor.validators import validate_row


def load_csv(file_path: str) -> list[dict]:
    """
    Read ticket data from a CSV file.

    Parameters:
        file_path: Path to the input CSV file.

    Returns:
        List of rows represented as dictionaries.

    Raises:
        FileNotFoundError: If input file does not exist.
        ValueError: If CSV file is empty.
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with path.open("r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        rows = list(reader)

    if not rows:
        raise ValueError("CSV file is empty")

    return rows


def calculate_sla_breach(
    created_at: str,
    sla_hours: float,
    status: str,
) -> bool:
    """
    Calculate whether a ticket breached SLA.

    Parameters:
        created_at: Ticket creation timestamp.
        sla_hours: Allowed SLA duration.
        status: Current ticket status.

    Returns:
        True if SLA is breached, otherwise False.
    """
    created_time = datetime.strptime(created_at, DATE_FORMAT)

    deadline = created_time + timedelta(hours=sla_hours)

    return deadline < datetime.now() and status.lower() != "closed"


def create_ticket(row: dict) -> Ticket:
    """
    Convert a valid CSV row into a Ticket object.

    Parameters:
        row: Valid ticket row.

    Returns:
        Ticket object.
    """
    priority = row["priority_raw"].lower()
    sla_hours = float(row["sla_hours"])

    return Ticket(
        ticket_id=row["ticket_id"],
        customer_name=row["customer_name"],
        category=row["category"],
        priority_raw=priority,
        priority_score=PRIORITY_MAP[priority],
        created_at=datetime.strptime(
            row["created_at"],
            DATE_FORMAT,
        ).isoformat(),
        sla_hours=sla_hours,
        status=row["status"],
        sla_breached=calculate_sla_breach(
            row["created_at"],
            sla_hours,
            row["status"],
        ),
    )


def process_tickets(
    rows: list[dict],
) -> tuple[list[Ticket], list[InvalidRow]]:
    """
    Validate and process ticket rows.

    Parameters:
        rows: Raw CSV rows.

    Returns:
        Tuple containing valid tickets and invalid rows.
    """
    tickets = []
    invalid_rows = []

    for row in rows:
        is_valid, reason = validate_row(row)

        if not is_valid:
            invalid_rows.append(
                InvalidRow(
                    raw_row=row,
                    reason=reason,
                )
            )
            continue

        tickets.append(create_ticket(row))

    return tickets, invalid_rows


def build_summary(
    total_rows: int,
    tickets: list[Ticket],
    invalid_rows: list[InvalidRow],
) -> dict:
    """
    Create ticket processing summary.

    Parameters:
        total_rows: Number of CSV rows processed.
        tickets: Valid ticket objects.
        invalid_rows: Invalid ticket rows.

    Returns:
        Summary dictionary.
    """
    category_count = Counter(
        ticket.category for ticket in tickets
    )

    breached_count = sum(
        ticket.sla_breached for ticket in tickets
    )

    return {
        "total_rows": total_rows,
        "valid_tickets": len(tickets),
        "invalid_rows": len(invalid_rows),
        "breached_count": breached_count,
        "by_category": dict(category_count),
    }


def check_abort_condition(
    total_rows: int,
    invalid_rows: list[InvalidRow],
) -> bool:
    """
    Check whether invalid row ratio exceeds allowed limit.

    Parameters:
        total_rows: Total rows processed.
        invalid_rows: Invalid row collection.

    Returns:
        True if processing should abort.
    """
    if total_rows == 0:
        return True

    invalid_ratio = len(invalid_rows) / total_rows

    return invalid_ratio > INVALID_ROW_ABORT_RATIO


def save_report(
    output_path: str,
    tickets: list[Ticket],
    invalid_rows: list[InvalidRow],
    summary: dict,
) -> None:
    """
    Write processed ticket report to JSON.

    Parameters:
        output_path: Destination JSON path.
        tickets: Valid tickets.
        invalid_rows: Invalid ticket rows.
        summary: Processing summary.

    Returns:
        None.
    """
    report = {
        "generated_at": datetime.now().isoformat(),
        "summary": summary,
        "tickets": [
            ticket.__dict__
            for ticket in tickets
        ],
        "invalid_rows": [
            invalid.__dict__
            for invalid in invalid_rows
        ],
    }

    with open(
        output_path,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            report,
            file,
            indent=4,
        )
