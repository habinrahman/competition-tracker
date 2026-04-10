from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Any

from common.fetcher import strip_google_placeholder_image
from common.news_media import extract_video_id


def _apply_youtube_thumb_if_missing(target: dict[str, Any], link: str) -> None:
    if (target.get("image") or "").strip():
        return
    if "youtube.com" not in link and "youtu.be" not in link:
        return
    vid = extract_video_id(link)
    if not vid:
        return
    target["image"] = f"https://img.youtube.com/vi/{vid}/hqdefault.jpg"


def _basic_normalize(title: str) -> str:
    t = (title or "").lower()

    # remove money
    t = re.sub(r"\$\d+[a-z]*|\₹\d+[a-z]*", "", t)

    # remove funding/action words
    remove_words = [
        "raises", "raised", "funding", "secures", "secured",
        "seed", "series", "round", "expands", "growth"
    ]

    for w in remove_words:
        t = t.replace(w, "")

    # remove punctuation
    t = re.sub(r"[^a-z0-9\s]", "", t)

    # normalize spaces
    t = re.sub(r"\s+", " ", t).strip()

    return t
def merge_similar_news(
    items: list[dict[str, Any]],
    *,
    similarity_threshold: float = 0.82,
) -> list[dict[str, Any]]:
    """
    Merge similar titles and group sources underneath one canonical title.

    Input: [{title, source, link}, ...]
    Output:
      [
        {"title": "...", "sources": [{"source": "...", "link": "..."}, ...]},
        ...
      ]
    """
    groups: list[dict[str, Any]] = []
    norm_titles: list[str] = []
    
    for it in items:
        title = (it.get("title") or "").strip()
        source = (it.get("source") or "Unknown").strip()
        link = (it.get("link") or "").strip()
        image = (it.get("image") or "").strip() or None
        desc = (it.get("description") or "").strip() or None
        published_at = it.get("published_at")
        if not title or not link:
            continue

        norm = _basic_normalize(title)

        best_idx = -1
        best_score = 0.0
        for idx, existing_norm in enumerate(norm_titles):
            entity1 = extract_main_entity(norm)
            entity2 = extract_main_entity(existing_norm)

            # If same company → force high similarity
            if entity1 and entity1 == entity2:
                score = 0.95
            else:
                score = SequenceMatcher(None, norm, existing_norm).ratio()
            if score > best_score:
                best_score = score
                best_idx = idx

        if best_idx >= 0 and best_score >= similarity_threshold:
            grp = groups[best_idx]
            # avoid duplicate source/link pairs
            if not any(s.get("link") == link for s in grp["sources"]):
                grp["sources"].append({"source": source, "link": link})
            if image and not (grp.get("image") or "").strip():
                grp["image"] = image
            if desc and not (grp.get("description") or "").strip():
                grp["description"] = desc
            if published_at is not None:
                gp = grp.get("published_at")
                if gp is None or published_at > gp:
                    grp["published_at"] = published_at
            _apply_youtube_thumb_if_missing(grp, link)
            continue

        row: dict[str, Any] = {"title": title, "sources": [{"source": source, "link": link}]}
        if image:
            row["image"] = image
        if desc:
            row["description"] = desc
        if published_at is not None:
            row["published_at"] = published_at
        _apply_youtube_thumb_if_missing(row, link)
        groups.append(row)
        norm_titles.append(norm)

    for grp in groups:
        strip_google_placeholder_image(grp)

    return groups


# --- EdTech-compat dedup (preserves existing behavior) ---

def normalize_title_edtech(title: str) -> str:
    """
    Must match the existing EdTech normalize_title() behavior exactly.
    """
    title = title.lower()
    title = re.sub(r"[^a-zA-Z\\s]", "", title)

    stopwords = ["the", "and", "for", "with", "to", "in", "of", "on", "at"]
    words = [w for w in title.split() if w not in stopwords]

    return " ".join(words[:6])


def is_duplicate_edtech(title: str, seen_keys: set[str]) -> bool:
    """
    Must match the existing EdTech is_duplicate() behavior exactly.
    """
    key = normalize_title_edtech(title)

    if key in seen_keys:
        return True

    seen_keys.add(key)
    return False

def extract_main_entity(title: str) -> str:
    words = title.lower().split()
    return words[0] if words else ""
