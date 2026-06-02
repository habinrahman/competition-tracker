from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from common.mass_sender import send_bulk
from common.weekly_newsletter import (
    build_weekly_newsletter_html,
    build_weekly_plain_text,
    fetch_merged_tech_news,
    weekly_subject,
)
from jobs.job_scraper import fetch_latest_jobs


def _parse_recipients(argv: list[str]) -> list[str]:
    if argv:
        emails = [a.strip() for a in argv if a.strip() and "@" in a]
        if emails:
            return emails

    env = (os.getenv("TEST_WEEKLY_RECIPIENTS") or "").strip()
    if env:
        emails = [x.strip() for x in env.split(",") if x.strip() and "@" in x]
        if emails:
            return emails

    raise ValueError(
        "Provide recipient emails as arguments or set TEST_WEEKLY_RECIPIENTS in .env"
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Send MicroDegree Weekly to specific addresses only (SES test send)."
    )
    parser.add_argument(
        "emails",
        nargs="*",
        help="Recipient emails (space-separated). Example: a@x.com b@y.com",
    )
    args = parser.parse_args()

    try:
        emails = _parse_recipients(args.emails)
    except ValueError as e:
        print(f"[WEEKLY TEST] ERROR: {e}")
        sys.exit(1)

    print("[WEEKLY TEST] Generating newsletter (test send only)...")
    print("[WEEKLY TEST] Recipients:", emails)

    jobs = fetch_latest_jobs(limit=6)
    if not jobs:
        print("[WEEKLY TEST] No jobs found. Aborting.")
        sys.exit(1)

    news = fetch_merged_tech_news()
    subject = f"[TEST] {weekly_subject()}"

    print(f"[WEEKLY TEST] Jobs: {len(jobs)} | News: {len(news)}")
    print("[WEEKLY TEST] Sending via SES...")

    send_bulk(
        emails,
        subject,
        build_html=lambda addr: build_weekly_newsletter_html(
            jobs,
            news,
            recipient_email=addr,
        ),
        build_plain=lambda addr: build_weekly_plain_text(
            jobs,
            news,
            recipient_email=addr,
        ),
    )

    print("[WEEKLY TEST] Done. No lock file written; full list was not emailed.")


if __name__ == "__main__":
    main()
