from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from common.emailer import build_feed_html
from common.mass_sender import send_bulk
from common.subscribers import get_emails
from domains.cloud_devops.tracker import fetch_cloud_news


def main():

    print("[MASS CLOUD] Generating newsletter...")

    news = fetch_cloud_news()
    subject = "Weekly Cloud Trends"

    print("[MASS CLOUD] Fetching subscribers...")

    emails = get_emails()

    # emails = emails[:5]

    print("[MASS CLOUD] Sending emails...")

    send_bulk(
        emails,
        subject,
        build_html=lambda addr: build_feed_html(
            news,
            title=subject,
            unsubscribe_recipient_email=addr,
        ),
    )

    print("[MASS CLOUD] Done.")


if __name__ == "__main__":
    main()
