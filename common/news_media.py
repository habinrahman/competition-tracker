from __future__ import annotations

import re
from typing import Any

from common.fetcher import fetch_article_metadata, strip_google_placeholder_image

# Google News RSS often attaches favicons / tiny icons — replace with real og:image from article.
_LOW_QUALITY_IMAGE_MARKERS = (
    "google.com/s2/favicons",
    "gstatic.com/faviconv2",
    "/favicon.ico",
    "favicon.ico?",
)


def _is_low_quality_feed_image(url: str) -> bool:
    u = (url or "").lower()
    return any(m in u for m in _LOW_QUALITY_IMAGE_MARKERS)


def extract_video_id(url: str) -> str | None:
    if not url:
        return None
    patterns = (
        r"v=([^&]+)",
        r"youtu\.be/([^?]+)",
        r"youtube\.com/embed/([^?/]+)",
        r"youtube\.com/shorts/([^?/]+)",
    )
    for p in patterns:
        m = re.search(p, url)
        if m:
            vid = m.group(1).strip()
            return vid or None
    return None


def _first_youtube_link(item: dict[str, Any]) -> str:
    candidates: list[str] = []
    pl = (item.get("link") or "").strip()
    if pl:
        candidates.append(pl)
    for s in item.get("sources") or []:
        if isinstance(s, dict):
            sl = (s.get("link") or "").strip()
            if sl:
                candidates.append(sl)
    for u in candidates:
        if "youtube.com" in u or "youtu.be" in u:
            return u
    return ""


def enrich_item_media(item: dict[str, Any]) -> None:
    """
    YouTube → real thumbnail URL; else keep RSS image or resolve og/twitter from link.
    No placeholder images.
    """
    item.pop("is_video", None)
    item.pop("video_link", None)
    item.pop("video_thumbnail", None)

    strip_google_placeholder_image(item)

    yt = _first_youtube_link(item)
    if yt:
        vid = extract_video_id(yt)
        if vid:
            item["image"] = f"https://img.youtube.com/vi/{vid}/hqdefault.jpg"
            return

    img = (item.get("image") or "").strip()
    if img and _is_low_quality_feed_image(img):
        item.pop("image", None)
        img = ""

    if img:
        item["image"] = img
        strip_google_placeholder_image(item)
        if item.get("image"):
            return

    primary = (item.get("link") or "").strip()
    if not primary and isinstance(item.get("sources"), list) and item["sources"]:
        primary = (item["sources"][0].get("link") or "").strip()

    if primary:
        meta = fetch_article_metadata(primary)
        if meta.get("image"):
            item["image"] = meta["image"]
        if meta.get("description"):
            item["description"] = meta["description"]
        strip_google_placeholder_image(item)
        if meta.get("image"):
            return

    item.pop("image", None)
