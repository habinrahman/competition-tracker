from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from common.mass_sender import send_bulk
from common.subscribers import get_emails
from jobs.job_emailer import generate_jobs_email
from jobs.job_scraper import fetch_latest_jobs


def main():

    print("[MASS JOBS] Generating job digest...")

    jobs = fetch_latest_jobs(limit=6)
    subject = "Weekly Job Updates"

    if not jobs:
        print("[MASS JOBS] No jobs found. Aborting.")
        return

    print("[MASS JOBS] Fetching subscribers...")

    emails = get_emails()

    # emails = emails[:5]

    print("[MASS JOBS] Sending emails...")

    send_bulk(
        emails,
        subject,
        build_html=lambda addr: generate_jobs_email(
            jobs,
            unsubscribe_recipient_email=addr,
        ),
    )

    print("[MASS JOBS] Done.")


if __name__ == "__main__":
    main()
