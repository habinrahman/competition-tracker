from __future__ import annotations

from dotenv import load_dotenv

load_dotenv()

from datetime import datetime, timedelta
from urllib.parse import urlparse

from common.article_image import enrich_news_items_with_images
from common.fetcher import fetch_rss_feed
from common.emailer import send_email
from common.logger import get_logger

from domains.cloud_devops.config import SUBJECT_PREFIX

logger = get_logger("cloud_devops")

CLOUD_SOURCES = [
    "https://aws.amazon.com/blogs/aws/feed/",
    "https://aws.amazon.com/blogs/devops/feed/",
    "https://devops.com/feed/",
    "https://kubernetes.io/feed.xml",
    "https://www.hashicorp.com/blog/rss.xml",
    "https://www.docker.com/blog/feed/",
    "https://github.blog/feed/",
    "https://cloud.google.com/blog/rss/",
    "https://devblogs.microsoft.com/devops/feed/",
]


def _safe_print(*args) -> None:
    try:
        print(*args)
    except UnicodeEncodeError:
        import sys

        enc = getattr(sys.stdout, "encoding", None) or "cp1252"
        safe_args = [str(a).encode(enc, "replace").decode(enc, "replace") for a in args]
        print(*safe_args)


def _domain_from_url(url: str) -> str:
    host = (urlparse(url).netloc or "").lower()
    if host.startswith("www."):
        host = host[4:]
    return host or "unknown"


def fetch_cloud_news() -> list[dict[str, str]]:
    seven_days_ago = datetime.now() - timedelta(days=7)
    staged: list[tuple[datetime | None, dict[str, str]]] = []

    for url in CLOUD_SOURCES:
        entries = fetch_rss_feed(url, limit=40, only_last_days=None)
        for entry in entries:
            published_at = entry.get("published_at")
            if published_at is not None and published_at < seven_days_ago:
                continue

            title = (entry.get("title") or "").strip()
            link = (entry.get("link") or "").strip()
            if not title or not link:
                continue

            source = (entry.get("source") or "").strip() or _domain_from_url(url)
            row: dict[str, str] = {
                "title": title,
                "link": link,
                "source": source,
            }

            _safe_print("Checking:", title)
            staged.append((published_at, row))

    staged.sort(
        key=lambda t: t[0] if t[0] is not None else datetime.min.replace(year=1900),
        reverse=True,
    )

    seen_links: set[str] = set()
    results: list[dict[str, str]] = []
    for _ts, row in staged:
        lk = row["link"]
        if lk in seen_links:
            continue
        seen_links.add(lk)
        results.append(row)

    top = results[:30]
    enrich_news_items_with_images(top, max_workers=5)
    return top


def run(*, recipients: list[str]) -> None:
    news = fetch_cloud_news()
    if not news:
        print("[cloud] No articles; exiting.")
        logger.info("No cloud articles.")
        return

    subject = f"{SUBJECT_PREFIX} ({datetime.now().date()})"
    send_email(news, subject, recipients)

    print("AWS DevOps email sent")
    logger.info("AWS DevOps email sent (%d stories).", len(news))
