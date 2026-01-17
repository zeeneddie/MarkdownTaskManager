# Datetime utilities for database compatibility
# Week 144: Timezone-naive datetime for PostgreSQL TIMESTAMP WITHOUT TIME ZONE columns
"""
This module provides timezone utilities to prevent the common error:
    "can't subtract offset-naive and offset-aware datetimes"

PostgreSQL TIMESTAMP WITHOUT TIME ZONE columns expect naive datetimes.
Using datetime.now(timezone.utc) creates timezone-aware datetimes which cause errors.

Use utc_now() instead of datetime.now(timezone.utc) for database operations.
"""

from datetime import datetime, timezone


def utc_now() -> datetime:
    """Return current UTC time as a naive datetime (no timezone info).

    Use this for database columns that are TIMESTAMP WITHOUT TIME ZONE.
    This prevents asyncpg errors with timezone-aware vs timezone-naive comparisons.

    Returns:
        datetime: Current UTC time without timezone info

    Example:
        # Instead of: datetime.now(timezone.utc)
        # Use: utc_now()

        created_at = utc_now()
    """
    return datetime.now(timezone.utc)


def ensure_naive(dt: datetime) -> datetime:
    """Convert a datetime to naive (remove timezone info) if it has one.

    Args:
        dt: A datetime that may or may not have timezone info

    Returns:
        datetime: The same datetime without timezone info
    """
    if dt is None:
        return None
    if dt.tzinfo is not None:
        # Convert to UTC then strip timezone
        return dt.replace(tzinfo=None)
    return dt
