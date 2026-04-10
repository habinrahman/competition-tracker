from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def ensure_when_7d(query: str) -> str:
    q = (query or "").strip()
    # Respect existing working queries that already include when:7d
    if "when:7d" in q.lower():
        return q
    return f"{q} when:7d".strip()


def safe_get(d: dict[str, Any], key: str, default: Any = None) -> Any:
    try:
        return d.get(key, default)
    except Exception:
        return default

