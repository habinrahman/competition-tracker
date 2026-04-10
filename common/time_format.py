from __future__ import annotations

from datetime import datetime
from typing import Any


def parse_published_value(value: Any) -> datetime | None:
    """Coerce JSON/datetime/string values from trackers or reports."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return None
        try:
            if s.endswith("Z"):
                s = s[:-1] + "+00:00"
            return datetime.fromisoformat(s)
        except ValueError:
            return None
    return None


def format_time_ago(dt: datetime | None) -> str:
    """
    Compact relative time for feed UI: 2h, 5h, 1d, etc.
    """
    if dt is None:
        return "—"

    now = datetime.now(dt.tzinfo) if getattr(dt, "tzinfo", None) else datetime.now()
    try:
        delta = now - dt
    except TypeError:
        return "—"

    secs = int(delta.total_seconds())
    if secs < 0:
        return "now"
    if secs < 3600:
        m = max(1, secs // 60)
        return f"{m}m"
    hours = secs // 3600
    if hours < 48:
        return f"{hours}h"
    days = secs // 86400
    return f"{max(1, days)}d"
