from __future__ import annotations

import random
import re
from typing import Any

_FILLER_PHRASES = re.compile(
    r"\b(reportedly|according to (?:sources?|reports?)|sources say|it appears that|"
    r"has been reported that|breaking\s*:|update\s*:|just in\s*[:\-]\s*)\s*",
    re.I,
)
_SOFT_VERB = re.compile(
    r"\b(research tools|new study finds|experts say|could potentially|may have|"
    r"might be|is said to)\s+",
    re.I,
)

_CURIOSITY = ("now", "quietly", "just")
_HOOK_PRESENT = re.compile(r"\b(quietly|just|now)\b", re.I)


def rewrite_title(title: str) -> str:
    """
    Sharp, insight-style line: strip fluff, tighten phrasing, optional curiosity hook.
    """
    t = (title or "").strip()
    if not t:
        return ""

    for sep in (" | ", " – ", " — "):
        if sep in t:
            left, right = t.split(sep, 1)
            r = right.strip()
            if len(r) < 44 and len(r.split()) <= 7:
                t = left.strip()
            break

    t = re.sub(r"\s*[-–—]\s*(Axios|Reuters|Bloomberg|TechCrunch|Verge|The Verge|"
               r"WSJ|FT|CNBC|Forbes|Wired|Ars Technica)\s*$", "", t, flags=re.I)

    t = _FILLER_PHRASES.sub("", t)
    t = _SOFT_VERB.sub("", t)

    t = re.sub(r"\bresearch shows\b", "signals", t, flags=re.I)
    t = re.sub(r"\bannounces\b", "rolls out", t, flags=re.I)
    t = re.sub(r"\blaunches\b", "introduces", t, flags=re.I)
    t = re.sub(r"\buses\b", "shifts to", t, flags=re.I)

    t = re.sub(r"\s+and\s+", " + ", t, flags=re.I)
    t = re.sub(r"\s+", " ", t).strip()

    if len(t) >= 50 and "demand" not in t.lower() and "surge" not in t.lower():
        if re.search(r"\b(hits?|reaches?|tops?)\s+\$?\d", t, re.I) and random.random() < 0.35:
            t = f"{t} as AI demand surges"

    if len(t.split()) >= 3 and not _HOOK_PRESENT.search(t) and random.random() < 0.38:
        parts = t.split(None, 1)
        if len(parts) == 2:
            t = f"{parts[0]} {random.choice(_CURIOSITY)} {parts[1]}"

    if len(t) > 90:
        cut = t[:90]
        sp = cut.rfind(" ")
        if sp > 52:
            cut = cut[:sp]
        t = cut.rstrip(" ,;—-|") + "…"

    return t


def shorten_feed_title(title: str) -> str:
    """Back-compat alias for templates still calling shorten_feed_title."""
    return rewrite_title(title)


def title_has_clear_signal(title: str) -> bool:
    t = (title or "").lower()
    needles = (
        "funding",
        "raises",
        "raised",
        "$",
        "million",
        "billion",
        "launch",
        "release",
        "model",
        "gpt",
        "claude",
        "anthropic",
        "openai",
        "acquisition",
        "acquire",
        "ipo",
        "lawsuit",
        "ban",
        "leak",
        "break",
        "security",
        "vulnerab",
        "benchmark",
        "google",
        "meta",
        "microsoft",
        "apple",
        "amazon",
        "nvidia",
    )
    return any(n in t for n in needles)


def should_include_insight(slot_index: int, item: dict[str, Any], why: str) -> bool:
    """Deprecated for email; kept for API compatibility."""
    return False


def prepare_feed_order(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Preserve ranked order (professional feed)."""
    return list(items)
