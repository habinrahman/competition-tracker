from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from common.mass_sender import send_bulk
from common.subscribers import get_emails
from common.weekly_newsletter import (
    build_weekly_newsletter_html,
    fetch_merged_tech_news,
    weekly_subject,
)
from jobs.job_scraper import fetch_latest_jobs


def main() -> None:
    print("[WEEKLY] Generating MicroDegree Weekly newsletter...")

    lock_path = PROJECT_ROOT / "logs" / "weekly_digest.lock"
    today = date.today().isoformat()
    if lock_path.exists() and lock_path.read_text(encoding="utf-8").strip() == today:
        print("[WEEKLY] Lock present for today; skipping send.")
        return

    jobs = fetch_latest_jobs(limit=6)
    if not jobs:
        print("[WEEKLY] No jobs found. Aborting.")
        return

    news = fetch_merged_tech_news()
    subject = weekly_subject()

    print(f"[WEEKLY] Jobs: {len(jobs)} | News: {len(news)}")
    print("[WEEKLY] Fetching subscribers...")

    emails = get_emails()
    if not emails:
        print("[WEEKLY] No active subscribers. Aborting.")
        return

    # emails = emails[:5]

    print("[WEEKLY] Sending emails...")

    send_bulk(
        emails,
        subject,
        build_html=lambda addr: build_weekly_newsletter_html(
            jobs,
            news,
            recipient_email=addr,
        ),
    )

    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text(today, encoding="utf-8")

    print("[WEEKLY] Done.")


if __name__ == "__main__":
    main()
