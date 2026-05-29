from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from common.emailer import send_gmail_html
from common.weekly_newsletter import (
    build_weekly_newsletter_html,
    fetch_merged_tech_news,
    weekly_subject,
)
from jobs.job_scraper import fetch_latest_jobs


def _preview_recipient() -> str:
    for key in ("PREVIEW_EMAIL", "TEST_EMAIL_RECIPIENT", "DEV_EMAIL", "SMTP_EMAIL"):
        value = (os.getenv(key) or "").strip()
        if value and "@" in value:
            return value
    raise ValueError(
        "Set PREVIEW_EMAIL in .env (or TEST_EMAIL_RECIPIENT / DEV_EMAIL / SMTP_EMAIL)."
    )


def main() -> None:
    print("[PREVIEW] Building MicroDegree Weekly preview...")

    jobs = fetch_latest_jobs(limit=6)
    if not jobs:
        print("[PREVIEW] No jobs found. Aborting.")
        return

    news = fetch_merged_tech_news()
    recipient = _preview_recipient()
    subject = f"[PREVIEW] {weekly_subject()}"
    html = build_weekly_newsletter_html(
        jobs,
        news,
        recipient_email=recipient,
    )

    print(f"[PREVIEW] Jobs: {len(jobs)} | News: {len(news)}")
    print(f"[PREVIEW] Sending via Gmail to: {recipient}")

    send_gmail_html(subject, html, [recipient])

    print("[PREVIEW] Done. Check your inbox before running run_mass_weekly.py.")


if __name__ == "__main__":
    main()
