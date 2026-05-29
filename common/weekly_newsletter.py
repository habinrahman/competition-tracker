from __future__ import annotations

from datetime import datetime
from html import escape
from typing import Any

from common.emailer import (
    _attr_url,
    _primary_link,
    _primary_source_label,
    build_weekly_unsubscribe_footer,
)
from domains.cloud_devops.tracker import fetch_cloud_news
from domains.genai.tracker import fetch_genai_news
from jobs.job_emailer import PORTAL_URL, build_job_cards_html

WEEKLY_NEWS_LIMIT = 15
WEEKLY_PREHEADER = (
    "This week's open roles and 15 curated GenAI and Cloud stories from MicroDegree."
)


def weekly_subject() -> str:
    month_year = datetime.now().strftime("%B %Y")
    return f"MicroDegree Weekly — Jobs & Tech Intelligence · {month_year}"


def _parse_published_at(item: dict[str, Any]) -> datetime:
    raw = item.get("published_at")
    if not raw:
        return datetime.min
    try:
        return datetime.fromisoformat(str(raw))
    except (TypeError, ValueError):
        return datetime.min


def fetch_merged_tech_news(*, limit: int = WEEKLY_NEWS_LIMIT) -> list[dict[str, Any]]:
    """Top ``limit`` GenAI + Cloud stories from the last 7 days, newest first."""
    combined: list[dict[str, Any]] = []
    seen_links: set[str] = set()

    for item in fetch_genai_news() + fetch_cloud_news():
        link = (item.get("link") or "").strip()
        if not link or link in seen_links:
            continue
        seen_links.add(link)
        combined.append(dict(item))

    combined.sort(key=_parse_published_at, reverse=True)
    return combined[:limit]


def _render_news_item_html(item: dict[str, Any], *, index: int) -> str:
    title_size = "16px" if index == 0 else "15px"
    title = escape((item.get("title") or "").strip())
    source = escape(_primary_source_label(item))
    link = _primary_link(item)

    if link:
        title_html = (
            f'<a href="{_attr_url(link)}" target="_blank" rel="noopener noreferrer" '
            f'style="color:#111827;text-decoration:none;">{title}</a>'
        )
        read_html = (
            f' <span style="color:#6b7280;">·</span> '
            f'<a href="{_attr_url(link)}" target="_blank" rel="noopener noreferrer" '
            f'style="color:#1a73e8;text-decoration:none;font-size:13px;">Read</a>'
        )
    else:
        title_html = title
        read_html = ""

    return f"""
    <div style="padding:12px 0;border-bottom:1px solid #e5e7eb;">
        <div style="font-size:{title_size};font-weight:600;line-height:1.45;color:#111827;">
            {title_html}{read_html}
        </div>
        <div style="font-size:12px;color:#6b7280;margin-top:4px;">{source}</div>
    </div>
    """


def build_weekly_newsletter_html(
    jobs: list[dict[str, Any]],
    news: list[dict[str, Any]],
    *,
    recipient_email: str,
) -> str:
    job_cards = build_job_cards_html(jobs)
    portal_h = _attr_url(PORTAL_URL)
    sent_on = escape(datetime.now().strftime("%d %B %Y"), quote=False)
    footer = build_weekly_unsubscribe_footer(recipient_email)

    news_block = ""
    if news:
        for index, item in enumerate(news):
            news_block += _render_news_item_html(item, index=index)
    else:
        news_block = (
            '<p style="margin:0;font-size:14px;color:#6b7280;">'
            "No tech updates this week."
            "</p>"
        )

    preheader = escape(WEEKLY_PREHEADER.strip())

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(weekly_subject())}</title>
</head>
<body style="margin:0;padding:0;background:#f4f6f8;font-family:Arial,Helvetica,sans-serif;">
  <div style="display:none;max-height:0;overflow:hidden;">{preheader}</div>
  <div style="max-width:600px;margin:0 auto;padding:24px 16px;">
    <div style="background:#ffffff;border-radius:8px;padding:24px 20px;border:1px solid #e5e7eb;">
      <p style="margin:0 0 8px;font-size:12px;letter-spacing:0.04em;text-transform:uppercase;color:#6b7280;">
        MicroDegree
      </p>
      <h1 style="margin:0 0 8px;font-size:22px;line-height:1.3;color:#111827;font-weight:700;">
        Your weekly update
      </h1>
      <p style="margin:0 0 24px;font-size:14px;line-height:1.55;color:#374151;">
        Jobs worth applying to, plus the most important GenAI and Cloud stories from the past week.
      </p>

      <h2 style="margin:0 0 12px;font-size:18px;color:#111827;border-bottom:2px solid #111827;padding-bottom:6px;">
        Job opportunities
      </h2>
      <p style="margin:0 0 16px;font-size:13px;color:#6b7280;">
        Six roles curated from the MicroDegree hiring portal.
      </p>
      {job_cards}
      <p style="margin:16px 0 28px;font-size:14px;">
        <a href="{portal_h}" target="_blank" rel="noopener noreferrer"
           style="color:#1a73e8;text-decoration:none;">View all jobs on MicroDegree →</a>
      </p>

      <h2 style="margin:0 0 12px;font-size:18px;color:#111827;border-bottom:2px solid #111827;padding-bottom:6px;">
        Tech intelligence
      </h2>
      <p style="margin:0 0 16px;font-size:13px;color:#6b7280;">
        Fifteen stories from GenAI and Cloud &amp; DevOps, ranked by date.
      </p>
      {news_block}

      {footer}

      <p style="margin:20px 0 0;font-size:12px;color:#9ca3af;text-align:center;">
        Sent on {sent_on}
      </p>
    </div>
  </div>
</body>
</html>"""
