from __future__ import annotations

import json
import os
from typing import Any


def _keyword_score_title(title: str) -> int:
    """Weighted fallback when OpenAI is unavailable or fails."""
    t = (title or "").lower()
    s = 0
    for w in ("launch", "release", "model"):
        if w in t:
            s += 3
    for w in ("funding", "raises"):
        if w in t:
            s += 3
    for w in ("acquisition", "merge"):
        if w in t:
            s += 2
    for w in ("kubernetes", "aws", "cloud"):
        if w in t:
            s += 2
    for w in ("ai", "llm"):
        if w in t:
            s += 1
    return s


def _keyword_rank(news: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(news, key=lambda it: _keyword_score_title((it.get("title") or "")), reverse=True)


def _apply_index_order(news: list[dict[str, Any]], order: list[Any]) -> list[dict[str, Any]]:
    n = len(news)
    seen: set[int] = set()
    out: list[dict[str, Any]] = []
    for raw in order:
        if not isinstance(raw, int):
            continue
        if 0 <= raw < n and raw not in seen:
            seen.add(raw)
            out.append(news[raw])
    for i in range(n):
        if i not in seen:
            out.append(news[i])
    return out


def rank_news(news: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Reorder items by founder-relevant importance.
    Uses OpenAI when OPENAI_API_KEY is set; otherwise keyword scoring.
    """
    if not news:
        return news

    if not (os.getenv("OPENAI_API_KEY") or "").strip():
        return _keyword_rank(news)

    try:
        from openai import OpenAI

        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        lines = [f"{i}: {(item.get('title') or '').strip()}" for i, item in enumerate(news)]
        body = "\n".join(lines)
        prompt = f"""Rank these news items by importance for a tech founder.

Criteria:
- product impact
- market impact
- technical breakthrough
- funding / acquisitions

News items (index: title):
{body}

Return a JSON object with key "order" whose value is an array of integers: indices from most important to least important. Each index must appear exactly once."""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content or "{}"
        data = json.loads(raw)
        order = data.get("order")
        if not isinstance(order, list):
            return _keyword_rank(news)
        reordered = _apply_index_order(news, order)
        return reordered
    except Exception as e:
        print("[rank_news] OpenAI error:", e)
        return _keyword_rank(news)
