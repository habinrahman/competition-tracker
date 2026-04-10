from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from domains.genai.tracker import fetch_genai_news
from domains.cloud_devops.tracker import fetch_cloud_news
from domains.edtech.tracker import fetch_edtech_news

from common.emailer import send_email


def build_combined_email(genai, cloud, edtech):

    html = "<h2>Weekly Intelligence Report</h2><hr>"

    # GenAI
    html += "<h3>🤖 GenAI</h3>"
    for item in genai:
        html += f'''
        <b>{item["title"]}</b><br>
        {item["source"]}<br>
        <a href="{item["link"]}">Read →</a><br><br>
        '''

    # Cloud
    html += "<h3>☁️ Cloud & DevOps</h3>"
    for item in cloud:
        html += f'''
        <b>{item["title"]}</b><br>
        {item["source"]}<br>
        <a href="{item["link"]}">Read →</a><br><br>
        '''

    # EdTech
    html += "<h3>🧠 EdTech</h3>"
    for item in edtech:
        html += f'''
        <b>{item["title"]}</b><br>
        {item["source"]}<br>
        <a href="{item["link"]}">Read →</a><br><br>
        '''

    return html


def main():
    genai = fetch_genai_news()
    cloud = fetch_cloud_news()
    edtech = fetch_edtech_news()

    html = build_combined_email(genai, cloud, edtech)

    import os

    recipients_env = (os.getenv("WEEKLY_RECIPIENTS") or "").strip()
    if not recipients_env:
        # Fallback: reuse existing per-domain recipients if set
        combined = ",".join(
            [
                os.getenv("GENAI_RECIPIENTS") or "",
                os.getenv("CLOUD_RECIPIENTS") or "",
                os.getenv("EDTECH_RECIPIENTS") or "",
            ]
        )
        recipients_env = combined

    recipients = [x.strip() for x in recipients_env.split(",") if x.strip()]
    if not recipients:
        raise ValueError(
            "Set WEEKLY_RECIPIENTS (or GENAI_RECIPIENTS/CLOUD_RECIPIENTS/EDTECH_RECIPIENTS) in .env"
        )

    send_email(
        genai + cloud + edtech,
        subject="Weekly Intelligence Report",
        recipients=recipients,
        html=html,
    )


if __name__ == "__main__":
    main()

