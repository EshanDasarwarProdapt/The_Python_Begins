"""
Small shared helpers and constants.

Single responsibility of this file: hold little pieces of logic that
don't belong to any one layer in particular (not database code, not
API-schema code, not routing code) - e.g. the list of valid statuses,
or a helper for building a "search" filter. Keeping these here avoids
duplicating them in multiple places.
"""

from sqlalchemy import or_

from app.models import Task

# Kept in sync with the `Literal` types in schemas.py. Useful anywhere
# we need to *iterate* over the allowed values (e.g. to build the
# `by_status` / `by_priority` dictionaries in the stats endpoint).
ALLOWED_PRIORITIES = ["Low", "Medium", "High"]
ALLOWED_STATUSES = ["Pending", "In Progress", "Completed"]


def apply_search_filter(query, search: str):
    """
    Given a SQLAlchemy query for Task and a search string, return a new
    query that only matches tasks whose title OR description contains
    that string (case-insensitive).

    Pulled out into its own function so the router/CRUD code that
    builds the `GET /tasks` filters doesn't get cluttered with SQL
    details - it just calls `apply_search_filter(query, search)`.
    """
    like_pattern = f"%{search}%"
    return query.filter(
        or_(
            Task.title.ilike(like_pattern),
            Task.description.ilike(like_pattern),
        )
    )
