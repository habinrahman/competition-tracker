from __future__ import annotations

import os
from datetime import datetime
from html import escape
from typing import Any

from common.unsubscribe_token import generate_token as _unsubscribe_token

PORTAL_URL = "https://portal.microdegree.work/jobs"


def _href(url: str) -> str:
    return escape(url or "", quote=True)


def _text(s: str) -> str:
    return escape((s or "").strip(), quote=False)


def generate_jobs_email(
    jobs: list[dict[str, Any]],
    *,
    unsubscribe_recipient_email: str | None = None,
) -> str:
    job_cards = ""

    for job in jobs:
        title = _text(str(job.get("title", "")))
        company = _text(str(job.get("company", "")))
        location = _text(str(job.get("location", "")))
        experience = _text(str(job.get("experience", "")))
        link = _href(str(job.get("link") or PORTAL_URL))

        job_cards += f"""
        <div style="border:1px solid #e5e7eb;border-radius:12px;
                    padding:16px;margin-bottom:16px;background:#ffffff;">
            <h3 style="margin:0;font-size:18px;">
                <a href="{link}" target="_blank" rel="noopener noreferrer"
                   style="text-decoration:none;color:#2563eb;">
                   {title}
                </a>
            </h3>
            <p style="margin:6px 0;"><strong>{company}</strong></p>
            <p style="margin:4px 0;">&#128205; {location}</p>
            <p style="margin:4px 0;">&#128188; Experience: {experience}</p>
            <a href="{link}" target="_blank" rel="noopener noreferrer"
               style="display:inline-block;margin-top:10px;
               padding:10px 16px;background:#2563eb;color:#fff;
               border-radius:8px;text-decoration:none;">
               Apply Now
            </a>
        </div>
        """

    portal_h = _href(PORTAL_URL)
    sent_on = escape(datetime.now().strftime("%d %B %Y"), quote=False)

    footer = ""
    if unsubscribe_recipient_email:
        base = (
            os.getenv("UNSUBSCRIBE_BASE_URL")
            or "https://newsletter.mddegree.in"
        ).rstrip("/")
        token = _unsubscribe_token(str(unsubscribe_recipient_email))
        unsub_url = f"{base}/unsubscribe?token={token}"
        footer = f"""
    <p style="margin-top:24px;padding-top:16px;border-top:1px solid #eee;font-size:11px;color:#999;line-height:1.5;text-align:center;">
        You are receiving this email because you subscribed to Microdegree Intelligence job updates.
    </p>
    <p style="font-size:11px;color:#999;text-align:center;">
        Microdegree Intelligence &bull; Weekly insights for builders
    </p>
    <p style="margin-top:12px;font-size:12px;color:#888;text-align:center;">
        <a href="{_href(unsub_url)}" style="color:#1a73e8;text-decoration:none;">Unsubscribe</a>
    </p>
    """

    html = f"""
    <html>
    <body style="font-family:Arial, Helvetica, sans-serif;background:#f4f6f8;padding:20px;margin:0;">
        <div style="max-width:600px;margin:0 auto;background:#ffffff;
                    border-radius:12px;padding:20px;">
            <h2 style="color:#111827;margin-top:0;">MicroDegree Weekly Job Updates</h2>
            <p style="color:#374151;">Explore the latest job opportunities curated for you.</p>

            {job_cards}

            <div style="text-align:center;margin-top:20px;">
                <a href="{portal_h}" target="_blank" rel="noopener noreferrer"
                   style="background:#111827;color:#ffffff;
                   padding:12px 20px;border-radius:8px;
                   text-decoration:none;display:inline-block;">
                   View More Jobs
                </a>
            </div>

            {footer}

            <p style="margin-top:20px;font-size:12px;color:#6b7280;text-align:center;">
                Sent on {sent_on}
            </p>
        </div>
    </body>
    </html>
    """

    return html
