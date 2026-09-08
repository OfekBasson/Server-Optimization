from datetime import datetime, timezone


def as_aware(dt: datetime) -> datetime:
    """Treat a naive datetime as UTC.

    Some DB backends (e.g. SQLite, used for quick local testing) don't
    persist timezone info even for a `DateTime(timezone=True)` column, so
    values read back can come back naive. Comparing/subtracting those
    against `datetime.now(timezone.utc)` raises a TypeError - route
    anything read from the DB through this first.
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt
