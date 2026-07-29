"""Build README demo assets (newsletter HTML + fixture cache).

Uses live MicroDegree jobs + RSS feeds when network is available.
Falls back to docs/demo/fixtures.json when offline.

No SMTP credentials required.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Required before importing common.emailer → unsubscribe_token
os.environ.setdefault("UNSUBSCRIBE_SECRET", "demo-readme-recording-secret")
os.environ.setdefault("UNSUBSCRIBE_BASE_URL", "http://127.0.0.1:8000")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from common.weekly_newsletter import (  # noqa: E402
    build_weekly_newsletter_html,
    fetch_merged_tech_news,
)
from jobs.job_scraper import fetch_latest_jobs  # noqa: E402

DEMO_DIR = PROJECT_ROOT / "docs" / "demo"
FIXTURES_PATH = DEMO_DIR / "fixtures.json"
NEWSLETTER_PATH = DEMO_DIR / "newsletter.html"
DEMO_RECIPIENT = "demo@example.com"


def _load_fixtures() -> tuple[list[dict], list[dict]]:
    payload = json.loads(FIXTURES_PATH.read_text(encoding="utf-8"))
    return payload["jobs"], payload["news"]


def _save_fixtures(jobs: list[dict], news: list[dict]) -> None:
    DEMO_DIR.mkdir(parents=True, exist_ok=True)
    FIXTURES_PATH.write_text(
        json.dumps({"jobs": jobs, "news": news}, indent=2),
        encoding="utf-8",
    )


def main() -> None:
    print("[DEMO] Building MicroDegree Weekly preview HTML...")

    jobs = fetch_latest_jobs(limit=6)
    news = fetch_merged_tech_news(limit=15)

    if jobs and news:
        print(f"[DEMO] Live fetch — jobs: {len(jobs)} | news: {len(news)}")
        _save_fixtures(jobs, news)
    elif FIXTURES_PATH.exists():
        print("[DEMO] Live fetch incomplete — using committed fixtures.json")
        jobs, news = _load_fixtures()
    else:
        raise SystemExit(
            "[DEMO] No live data and no fixtures.json. Connect to the network once to seed fixtures."
        )

    if not jobs:
        raise SystemExit("[DEMO] No jobs available for newsletter preview.")

    html = build_weekly_newsletter_html(jobs, news, recipient_email=DEMO_RECIPIENT)
    DEMO_DIR.mkdir(parents=True, exist_ok=True)
    NEWSLETTER_PATH.write_text(html, encoding="utf-8")
    print(f"[DEMO] Wrote {NEWSLETTER_PATH.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
