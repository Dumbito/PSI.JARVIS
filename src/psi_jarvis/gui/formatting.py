"""Shared, human-friendly formatting helpers for the GUI layer.

These helpers only affect presentation. They never alter, round or
reinterpret persisted scientific data - they format it for display.
"""

from datetime import datetime


def format_timestamp(value: datetime) -> str:
    """Render a timestamp as a compact, human-readable string.

    Full precision (microseconds, UTC offset) is preserved in the
    persisted data and in exports; this is a display-only shortening
    so timestamps fit table columns and remain scannable.
    """
    return value.strftime("%Y-%m-%d %H:%M")


def format_timestamp_str(value: str) -> str:
    """Format an already-persisted ISO timestamp string for display.

    Some repositories persist timestamps as ISO 8601 strings rather
    than ``datetime`` objects. This renders them the same way as
    :func:`format_timestamp`, falling back to the raw value if it
    cannot be parsed (e.g. unexpected legacy formats), so a display
    quirk never hides or corrupts the underlying persisted evidence.
    """
    try:
        return format_timestamp(datetime.fromisoformat(value))
    except ValueError:
        return value
