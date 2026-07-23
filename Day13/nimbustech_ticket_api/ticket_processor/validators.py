from datetime import datetime

from ticket_processor.config import (
    DATE_FORMAT,
    REQUIRED_COLUMNS,
    VALID_PRIORITIES,
)


def validate_required_fields(row: dict) -> tuple[bool, str]:
    """
    Validate that required ticket fields are present.

    Parameters:
        row: Dictionary containing CSV row data.

    Returns:
        Tuple containing validation status and error reason.
    """
    for field in REQUIRED_COLUMNS:
        if not row.get(field):
            return False, f"missing {field}"

    return True, ""


def validate_priority(priority: str) -> tuple[bool, str]:
    """
    Validate ticket priority value.

    Parameters:
        priority: Raw priority value from CSV.

    Returns:
        Tuple containing validation status and error reason.
    """
    if priority.lower() not in VALID_PRIORITIES:
        return False, "invalid priority value"

    return True, ""


def validate_sla_hours(sla_hours: str) -> tuple[bool, str]:
    """
    Validate SLA hours value.

    Parameters:
        sla_hours: SLA duration from CSV.

    Returns:
        Tuple containing validation status and error reason.
    """
    try:
        value = float(sla_hours)

        if value <= 0:
            return False, "sla_hours must be positive"

    except (ValueError, TypeError):
        return False, "sla_hours must be a number"

    return True, ""


def validate_created_at(created_at: str) -> tuple[bool, str]:
    """
    Validate ticket creation date format.

    Parameters:
        created_at: Ticket creation timestamp.

    Returns:
        Tuple containing validation status and error reason.
    """
    try:
        datetime.strptime(created_at, DATE_FORMAT)

    except ValueError:
        return False, "invalid created_at date"

    return True, ""


def validate_row(row: dict) -> tuple[bool, str]:
    """
    Run all validation checks for a CSV row.

    Parameters:
        row: Dictionary containing ticket information.

    Returns:
        Tuple containing validation status and error reason.
    """
    is_valid, reason = validate_required_fields(row)

    if not is_valid:
        return False, reason

    validators = [
        lambda data: validate_priority(data["priority_raw"]),
        lambda data: validate_sla_hours(data["sla_hours"]),
        lambda data: validate_created_at(data["created_at"]),
    ]

    for validator in validators:
        is_valid, reason = validator(row)

        if not is_valid:
            return False, reason

    return True, ""
