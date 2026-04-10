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
from domains.genai.tracker import fetch_genai_news


def main():

    print("[MASS GENAI] Generating newsletter...")

    # Gmail `run()` is not used here (requires recipients, returns None).
    news = fetch_genai_news()
    subject = "Weekly AI Trends"

    print("[MASS GENAI] Fetching subscribers...")

    emails = get_emails()

    # Testing: uncomment to limit sends before full run
    # emails = emails[:5]

    print("[MASS GENAI] Sending emails...")

    send_bulk(
        emails,
        subject,
        build_html=lambda addr: build_feed_html(
            news,
            title=subject,
            unsubscribe_recipient_email=addr,
        ),
    )

    print("[MASS GENAI] Done.")


if __name__ == "__main__":
    main()
