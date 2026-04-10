from __future__ import annotations

from dotenv import load_dotenv

load_dotenv()

from datetime import datetime, timedelta
import os
import json

from common.article_image import enrich_news_items_with_images
from common.dedup import is_duplicate_edtech
from common.fetcher import fetch_google_news_rss
from common.logger import get_logger
from common.emailer import send_email

from domains.edtech.config import QUERY, HL, GL, CEID, SUBJECT_PREFIX


logger = get_logger("edtech")


def _safe_print(*args) -> None:
    """
    Windows console can choke on some Unicode (e.g. ₹). This keeps the tracker
    cron-safe without changing business logic.
    """
    try:
        print(*args)
    except UnicodeEncodeError:
        import sys

        enc = (getattr(sys.stdout, "encoding", None) or "cp1252")
        safe_args = []
        for a in args:
            s = str(a)
            # Convert to something the current console encoding can print.
            safe_args.append(s.encode(enc, "replace").decode(enc, "replace"))
        print(*safe_args)


def fetch_edtech_news():
    """
    Simple fetcher:
    - 7-day filter
    - basic duplicate suppression within this run
    Returns only: title, source, link
    """
    results: list[dict[str, str]] = []
    seen_keys: set[str] = set()
    seven_days_ago = datetime.now() - timedelta(days=7)

    entries = fetch_google_news_rss(
        QUERY,
        limit=25,
        hl=HL,
        gl=GL,
        ceid=CEID,
        only_last_days=None,  # keep original logic below
    )

    for entry in entries:
        title = entry["title"]
        link = entry["link"]
        source = entry.get("source") or "Unknown"

        _safe_print("Checking:", title)

        # ✅ filter old news (preserve original behavior)
        published_at = entry.get("published_at")
        if published_at is not None and published_at < seven_days_ago:
            _safe_print("Skipped old:", title)
            continue

        # ✅ dedup (preserve original behavior)
        if is_duplicate_edtech(title, seen_keys):
            _safe_print("Skipped duplicate:", title)
            continue

        results.append({"title": title, "source": source, "link": link})

    enrich_news_items_with_images(results, max_workers=5)
    return results


def generate_reports(news):
    # Kept verbatim (paths + markdown format) to avoid breaking existing workflow.
    today = datetime.now().date()

    os.makedirs("reports", exist_ok=True)

    json_file = f"reports/funding_report_{today}.json"
    md_file = f"reports/funding_report_{today}.md"

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(news, f, indent=4, ensure_ascii=False)

    with open(md_file, "w", encoding="utf-8") as f:
        f.write(f"🧠 Weekly EdTech Intelligence – India ({today})\n\n")
        f.write("=" * 50 + "\n\n")

        if not news:
            f.write("No relevant EdTech news found.\n")
        else:
            for i, item in enumerate(news, 1):
                f.write(f"{i}. {item['title']}\n")
                f.write(f"Source: {item['source']}\n")
                f.write(f"Read: {item['link']}\n")
                f.write("-" * 40 + "\n\n")

    print(f"Reports saved:\n- {json_file}\n- {md_file}")


def run(*, recipients: list[str]) -> None:
    """
    New production runner-compatible entrypoint:
    - No state tracking: every run includes last 7 days.
    - No enrichment/ranking: only title/link/source.
    """
    news = fetch_edtech_news()
    if not news:
        print("[edtech] No articles; exiting.")
        logger.info("No EdTech articles.")
        return

    today = datetime.now().date()
    subject = f"{SUBJECT_PREFIX} ({today})"
    send_email(news, subject, recipients)
    logger.info("Sent %d EdTech items.", len(news))


if __name__ == "__main__":
    # Keep the historical behavior (generate reports) when executed directly.
    news = fetch_edtech_news()
    generate_reports(news)
