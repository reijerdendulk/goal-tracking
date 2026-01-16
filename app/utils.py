from datetime import datetime, timedelta


def compute_duration_min(start_at: datetime, end_at: datetime | None) -> int | None:
    """
    Compute duration in minutes from start and end times.

    Returns None if end_at is not provided.
    """
    if end_at is None:
        return None
    delta = end_at - start_at
    return int(delta.total_seconds() / 60)


def get_week_start(dt: datetime) -> datetime:
    """
    Get the start of the week (Monday) for a given datetime.

    Returns a datetime at 00:00:00 on the Monday of the week.
    """
    days_since_monday = dt.weekday()
    week_start = dt - timedelta(days=days_since_monday)
    return week_start.replace(hour=0, minute=0, second=0, microsecond=0)


def format_week_start(dt: datetime) -> str:
    """Format a datetime as ISO date string (YYYY-MM-DD)."""
    return dt.strftime("%Y-%m-%d")
