"""
Configuration constants for the NimbusTech ticket processor.
"""

PRIORITY_MAP = {
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}

VALID_PRIORITIES = set(PRIORITY_MAP.keys())

INVALID_ROW_ABORT_RATIO = 0.10

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

REQUIRED_COLUMNS = {
    "ticket_id",
    "customer_name",
    "category",
    "priority_raw",
    "created_at",
    "sla_hours",
    "status",
}
