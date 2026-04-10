from __future__ import annotations

import os
import re


def _strip_leading_arrow(s: str) -> str:
    return re.sub(r"^[→\-\*\s]+", "", (s or "").strip())


def _clamp_words(s: str, max_words: int) -> str:
    words = (s or "").split()
    if len(words) <= max_words:
        return " ".join(words)
    return " ".join(words[:max_words]).rstrip(",.;:") + "…"


def _heuristic_insight(title: str) -> str:
    tl = (title or "").lower()
    if "launch" in tl:
        return "New product launch"
    if "model" in tl:
        return "New AI capability"
    if "funding" in tl:
        return "Investor interest rising"
    return ""


_BANNED_TOKENS = re.compile(
    r"\b(enhances?|improving|improves|efficiency|innovation|leverage|synergy|"
    r"robust|seamless|cutting[- ]edge|empower|unlock|delve|landscape)\b",
    re.I,
)


def _sanitize_insight_line(line: str) -> str:
    line = _strip_leading_arrow(line)
    if _BANNED_TOKENS.search(line):
        return ""
    return _clamp_words(line, 8)


def generate_insight(title: str) -> str:
    """
    Max ~8 words, punchy (no generic AI tone). No API key → keyword heuristic or "".
    """
    t = (title or "").strip()
    if not t:
        return ""

    if not (os.getenv("OPENAI_API_KEY") or "").strip():
        return _heuristic_insight(t)

    try:
        from openai import OpenAI

        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Write ONE punchy label for a founder feed (MAX 8 words). "
                        "No filler. Do NOT use: enhances, improves, efficiency, innovation, "
                        "leverage, synergy, seamless, cutting-edge, empower.\n"
                        "Style like: 'Competes with OpenAI', 'New AI dev tool', "
                        "'Signals funding shift', 'Security risk exposed'.\n\n"
                        f"Headline: {t}"
                    ),
                }
            ],
            temperature=0.35,
            max_tokens=40,
        )
        line = (response.choices[0].message.content or "").strip()
        line = line.split("\n")[0].strip()
        cleaned = _sanitize_insight_line(line)
        if cleaned:
            return cleaned
        return _heuristic_insight(t)
    except Exception as e:
        print("[generate_insight] error:", e)
        return _heuristic_insight(t)
