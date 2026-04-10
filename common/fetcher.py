from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any
from urllib.parse import parse_qs, quote, unquote, urlparse

import feedparser
from bs4 import BeautifulSoup

from common.utils import ensure_when_7d


@dataclass(frozen=True)
class NewsItem:
    title: str
    source: str
    link: str
    published_at: datetime | None = None


def extract_feed_entry_image(entry: Any) -> str | None:
    """
    Best-effort image URL from a feedparser entry (RSS/Atom).
    Tries: image, media_content, media_thumbnail, enclosure links.
    """
    img = getattr(entry, "image", None)
    if img:
        if isinstance(img, dict):
            u = img.get("href") or img.get("url")
            if u:
                return str(u).strip() or None
        href = getattr(img, "href", None) or getattr(img, "url", None)
        if href:
            return str(href).strip() or None

    media_content = getattr(entry, "media_content", None) or []
    first_media_url: str | None = None
    for mc in media_content:
        if isinstance(mc, dict):
            u = mc.get("url") or mc.get("href")
            if not u:
                continue
            u = str(u).strip()
            if not first_media_url:
                first_media_url = u
            typ = str(mc.get("type", "")).lower()
            med = str(mc.get("medium", "")).lower()
            if typ.startswith("image/") or med == "image" or "image" in typ:
                return u
        else:
            u = getattr(mc, "url", None) or getattr(mc, "href", None)
            if u:
                return str(u).strip() or None
    if first_media_url:
        return first_media_url

    thumbs = getattr(entry, "media_thumbnail", None) or []
    for th in thumbs:
        if isinstance(th, dict):
            u = th.get("url")
            if u:
                return str(u).strip() or None
        elif getattr(th, "url", None):
            return str(th.url).strip() or None

    for link in getattr(entry, "links", None) or []:
        if not isinstance(link, dict):
            continue
        if link.get("rel") == "enclosure" and str(link.get("type", "")).startswith("image/"):
            u = link.get("href") or link.get("url")
            if u:
                return str(u).strip() or None

    return None


def extract_real_url(url: str) -> str:
    import requests

    try:
        headers = {"User-Agent": "Mozilla/5.0"}

        response = requests.get(url, headers=headers, timeout=5)
        html = response.text

        soup = BeautifulSoup(html, "html.parser")

        # STEP 1 — canonical link (robust)
        canonical = soup.find("link", rel="canonical")
        if canonical and canonical.get("href"):
            real_url = str(canonical["href"]).strip()

            if "news.google.com" not in real_url:
                return real_url

        # STEP 2 — url= parameter fallback
        parsed = urlparse(url)
        query = parse_qs(parsed.query)

        if "url" in query:
            real_url = unquote(query["url"][0])

            if real_url.startswith("http"):
                return real_url

        # STEP 3 — final redirect fallback
        final = response.url

        if "news.google.com" not in final:
            return final

        print("[WARN] could not resolve:", url)
        return url

    except Exception as e:
        print("[extract_error]", e)
        return url


def resolve_final_url(url: str) -> str:
    import requests

    try:
        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        # Try HEAD first (fast)
        response = requests.head(
            url,
            allow_redirects=True,
            timeout=5,
            headers=headers
        )

        if response.url and "news.google.com" not in response.url:
            return response.url

        # Fallback to GET
        response = requests.get(
            url,
            allow_redirects=True,
            timeout=5,
            headers=headers
        )

        return response.url

    except Exception as e:
        print("[resolve_error]", e)
        return url


def strip_google_placeholder_image(item: dict[str, Any]) -> None:
    """Drop favicon/gstatic/Google News icon URLs masquerading as hero images."""
    img = item.get("image")
    if not isinstance(img, str) or not img.strip():
        return
    il = img.lower()
    if "gstatic" in il or "google" in il:
        item.pop("image", None)


def enrich_flat_rss_item(item: dict[str, Any]) -> None:
    """
    Resolve Google News redirect URLs and merge og/twitter metadata into a flat fetch row.
    Call once per item after RSS fetch, before merge_similar_news.
    """
    link = (item.get("link") or "").strip()
    if not link:
        return

    real_url = extract_real_url(link)
    if "news.google.com" in real_url:
        print("[WARN] still google URL:", real_url)
    meta = fetch_article_metadata(real_url)
    item["link"] = real_url

    if meta:
        if meta.get("title"):
            item["title"] = meta["title"]
        if meta.get("image"):
            item["image"] = meta["image"]
        if meta.get("description"):
            item["description"] = meta["description"]

    strip_google_placeholder_image(item)


def fetch_article_metadata(url: str, *, timeout: float = 6.0) -> dict[str, Any]:
    """
    Fetch publisher page once; extract og/twitter title, image, description.
    Returns {} on failure. Image is a real article thumbnail when publishers expose og:image.
    """
    import requests
    from bs4 import BeautifulSoup

    out: dict[str, Any] = {}
    if not (url or "").strip():
        return out

    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
        }
        res = requests.get(url.strip(), headers=headers, timeout=timeout, allow_redirects=True)
        if res.status_code >= 400 or not res.text:
            return out

        html = res.text[:800_000]
        soup = BeautifulSoup(html, "html.parser")

        def get_meta_property(prop: str) -> str | None:
            tag = soup.find("meta", property=prop)
            if tag and tag.get("content"):
                return str(tag["content"]).strip()
            return None

        def get_meta_name(name: str) -> str | None:
            tag = soup.find("meta", attrs={"name": name})
            if tag and tag.get("content"):
                return str(tag["content"]).strip()
            return None

        title = (
            get_meta_property("og:title")
            or get_meta_name("twitter:title")
        )
        if not title and soup.title and soup.title.string:
            title = str(soup.title.string).strip()

        image = (
            get_meta_property("og:image")
            or get_meta_property("og:image:url")
            or get_meta_name("twitter:image")
            or get_meta_name("twitter:image:src")
        )
        if not image:
            tw = soup.find("meta", property="twitter:image")
            if tw and tw.get("content"):
                image = str(tw["content"]).strip()

        description = (
            get_meta_property("og:description")
            or get_meta_name("twitter:description")
        )

        if title:
            out["title"] = title
        if image and image.startswith("http"):
            out["image"] = image
        if description:
            out["description"] = description

        return out
    except Exception:
        return out


def scrape_og_twitter_image(url: str, *, timeout: float = 6.0) -> str | None:
    """Resolve og:image / twitter:image via a single article fetch."""
    meta = fetch_article_metadata(url, timeout=timeout)
    img = meta.get("image")
    if isinstance(img, str) and img.startswith("http"):
        return img
    return None


def extract_entry_image(entry: Any, link: str) -> str | None:
    """
    RSS-native image first, then page meta (og/twitter) from canonical link.
    """
    u = extract_feed_entry_image(entry)
    if u:
        return u
    return scrape_og_twitter_image(link)


def fetch_rss_feed(
    url: str,
    *,
    limit: int = 20,
    only_last_days: int | None = None,
) -> list[dict[str, Any]]:
    """
    Generic RSS/Atom fetch; same item shape as fetch_google_news_rss for pipeline reuse.
    """
    feed = feedparser.parse(url)
    cutoff: datetime | None = None
    if only_last_days is not None:
        cutoff = datetime.now() - timedelta(days=int(only_last_days))

    items: list[dict[str, Any]] = []
    for entry in (feed.entries or [])[: int(limit)]:
        title = getattr(entry, "title", "") or ""
        link = getattr(entry, "link", "") or ""
        source = "Unknown"
        if hasattr(entry, "source") and getattr(entry.source, "title", None):
            source = entry.source.title
        elif getattr(feed, "feed", None) and getattr(feed.feed, "title", None):
            source = str(feed.feed.title)

        published_at: datetime | None = None
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            try:
                published_at = datetime(*entry.published_parsed[:6])
            except Exception:
                published_at = None

        if cutoff is not None and published_at is not None and published_at < cutoff:
            continue

        if not title or not link:
            continue

        image = extract_feed_entry_image(entry)
        row: dict[str, Any] = {
            "title": title,
            "source": source,
            "link": link,
            "published_at": published_at,
        }
        if image:
            row["image"] = image
        items.append(row)

    return items


def fetch_google_news_rss(
    query: str,
    *,
    limit: int = 25,
    hl: str = "en-IN",
    gl: str = "IN",
    ceid: str = "IN:en",
    only_last_days: int | None = 7,
) -> list[dict[str, Any]]:
    """
    Fetch Google News RSS results for a query.

    Returns list of dicts (at minimum): {title, source, link}
    Also includes optional: {published_at}
    """
    q = ensure_when_7d(query)
    rss_url = f"https://news.google.com/rss/search?q={quote(q)}&hl={hl}&gl={gl}&ceid={ceid}"
    feed = feedparser.parse(rss_url)

    cutoff: datetime | None = None
    if only_last_days is not None:
        cutoff = datetime.now() - timedelta(days=int(only_last_days))

    items: list[dict[str, Any]] = []
    for entry in (feed.entries or [])[: int(limit)]:
        title = getattr(entry, "title", "") or ""
        link = getattr(entry, "link", "") or ""
        source = "Unknown"
        if hasattr(entry, "source") and getattr(entry.source, "title", None):
            source = entry.source.title

        published_at: datetime | None = None
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            try:
                published_at = datetime(*entry.published_parsed[:6])
            except Exception:
                published_at = None

        if cutoff is not None and published_at is not None and published_at < cutoff:
            continue

        if not title or not link:
            continue

        image = extract_feed_entry_image(entry)

        row: dict[str, Any] = {
            "title": title,
            "source": source,
            "link": link,
            "published_at": published_at,
        }
        if image:
            row["image"] = image
        items.append(row)

    return items

