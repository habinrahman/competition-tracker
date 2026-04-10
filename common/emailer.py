from __future__ import annotations

from dotenv import load_dotenv

load_dotenv()

import json
import os
import smtplib
from datetime import datetime
from email.message import EmailMessage
from html import escape
from typing import Any
from common.unsubscribe_token import generate_token as _unsubscribe_token

MAX_FEED_ITEMS = 5

_TAGLINE = "High-signal updates worth your attention"


def _attr_url(url: str) -> str:
    return escape(url, quote=True)


def _primary_link(item: dict[str, Any]) -> str:
    link = (item.get("link") or "").strip()
    if link:
        return link
    for s in item.get("sources") or []:
        if isinstance(s, dict):
            sl = (s.get("link") or "").strip()
            if sl:
                return sl
    return ""


def _primary_source_label(item: dict[str, Any]) -> str:
    if isinstance(item.get("sources"), list) and item["sources"]:
        s0 = item["sources"][0]
        if isinstance(s0, dict):
            return (s0.get("source") or "Source").strip() or "Source"
    return (item.get("source") or "Source").strip() or "Source"


def _render_feed_item_html(item: dict[str, Any]) -> str:
    # Legacy helper kept for backwards compatibility with older templates.
    # (Images intentionally not rendered; this system is text-only.)
    title = escape((item.get("title") or "").strip())
    src = escape(_primary_source_label(item))
    link = _primary_link(item)
    read_more = (
        f'<a href="{_attr_url(link)}" style="color:#1a73e8;text-decoration:none;">Read →</a>'
        if link
        else ""
    )

    return f"""
    <div style="padding:10px 0;border-bottom:1px solid #eee;">
        <div style="font-size:15px;font-weight:600;line-height:1.4;margin-bottom:4px;">
            {title}
        </div>
        <div style="font-size:12px;color:#777;margin-bottom:6px;">
            {src}
        </div>
        {read_more}
    </div>
    """


def build_feed_html(
    news: list[dict[str, Any]],
    *,
    title: str,
    unsubscribe_recipient_email: str | None = None,
) -> str:
    content = ""

    # STEP 2 — HEADER IMPROVEMENT
    content += f"""
    <h2 style="
        margin-bottom: 4px;
        font-size: 20px;
    ">
        {escape(str(title).strip())}
    </h2>

    <p style="
        margin-top: 0;
        color: #666;
        font-size: 13px;
    ">
        Handpicked signals worth your attention
    </p>

    <hr style="margin:12px 0;">
    """

    if not news:
        content += '<div style="font-size:13px;color:#666;">No updates right now.</div>'
    else:
        # STEP 3 — CONVERT ITEMS INTO CARDS (+ STEP 5 first item bigger)
        for index, item in enumerate(news):
            title_size = "17px" if index == 0 else "15px"
            t = escape((item.get("title") or "").strip())
            s = escape(_primary_source_label(item))
            link = _primary_link(item)
            if link:
                title_html = f"""
                    <a href="{_attr_url(link)}" target="_blank" style="
                        color: #111827;
                        text-decoration: none;
                        display: inline-block;
                    ">
                        {t}
                    </a>
                """
            else:
                title_html = t
            link_html = (
                f"""
                <a href="{_attr_url(link)}" style="
                    font-size: 12px;
                    text-decoration: none;
                    color: #1a73e8;
                ">
                    Read →
                </a>
                """
                if link
                else ""
            )

            image_block = ""
            if item.get("image"):
                img = str(item["image"]).strip()
                img_lower = img.lower()
                if (
                    img
                    and img.startswith("http")
                    and "google" not in img_lower
                    and "gstatic" not in img_lower
                ):
                    image_block = f"""<img src="{_attr_url(img)}" style="
            width:100%;
            max-width:600px;
            border-radius:6px;
            margin-bottom:8px;
            display:block;
        " alt="News Image">
        """

            content += f"""
            <div style="
                padding: 10px 0;
                border-bottom: 1px solid #eee;
            ">
                {image_block}
                <div style="
                    font-size: {title_size};
                    font-weight: 600;
                    line-height: 1.4;
                    margin-bottom: 4px;
                ">
                    {title_html}
                </div>

                <div style="
                    font-size: 12px;
                    color: #777;
                    margin-bottom: 6px;
                ">
                    {s}
                </div>

                {link_html}
            </div>
            """

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
        You are receiving this because you subscribed to Microdegree Intelligence.
    </p>
    <p style="font-size:11px;color:#999;text-align:center;">
        Microdegree Intelligence &bull; Weekly insights for builders
    </p>
    <p style="margin-top:12px;font-size:12px;color:#888;text-align:center;">
        <a href="{_attr_url(unsub_url)}" style="color:#1a73e8;text-decoration:none;">Unsubscribe</a>
    </p>
    """

    # STEP 1 — ADD CONTAINER
    html = f"""
    <div style="
        font-family: Arial, sans-serif;
        max-width: 600px;
        margin: auto;
        padding: 16px;
    ">
        {content}
        {footer}
    </div>
    """

    return f"<html><body style=\"margin:0;padding:0;\">{html}</body></html>"


def _dev_mode_enabled() -> bool:
    v = (os.getenv("DEV_MODE") or "").strip().lower()
    return v in ("1", "true", "yes", "on")


FOUNDER_EMAILS = [
    "habin936@gmail.com",
]

DEV_EMAIL = "habin936@gmail.com"

SENDER_EMAIL = os.getenv("SMTP_EMAIL")
SENDER_PASSWORD = os.getenv("SMTP_PASSWORD")


def _mask_email(email: str | None) -> str:
    if not email:
        return "<missing>"
    if "@" not in email:
        return email[:2] + "***"
    name, domain = email.split("@", 1)
    if len(name) <= 2:
        masked_name = name[:1] + "***"
    else:
        masked_name = name[:2] + "***" + name[-1:]
    return f"{masked_name}@{domain}"


def _has_password(pw: str | None) -> bool:
    return bool(pw and str(pw).strip())


def _send_html(subject: str, html: str, recipients: list[str]) -> None:
    sender_email = os.getenv("SMTP_EMAIL")
    sender_password = os.getenv("SMTP_PASSWORD")

    print("[email] SMTP_EMAIL:", _mask_email(sender_email))
    print("[email] SMTP_PASSWORD present:", _has_password(sender_password))

    if not sender_email or not _has_password(sender_password):
        print("[email] ERROR: Missing SMTP credentials (SMTP_EMAIL/SMTP_PASSWORD).")
        return

    if not subject or not str(subject).strip():
        print("[email] ERROR: Missing subject.")
        return
    if not html or not str(html).strip():
        print("[email] ERROR: Empty HTML body.")
        return
    if not recipients:
        print("[email] ERROR: No recipients provided.")
        return

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = ", ".join(recipients)
    msg.set_content("Your email client does not support HTML.")
    msg.add_alternative(html, subtype="html")

    try:
        print("[email] Connecting to SMTP (smtp.gmail.com:465)...")
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as server:
            print("[email] Logging in...")
            server.login(sender_email, sender_password)
            print("[email] Login succeeded.")
            server.send_message(msg)
            print("[email] Email sent successfully.")

        print("[email] Email sent to:", recipients)
    except Exception as e:
        print("[email] EMAIL ERROR:", str(e))
        return


def build_edtech_html(
    news: list[dict[str, Any]] | dict[str, Any] | None = None,
    *,
    top: list[dict[str, Any]] | None = None,
    other: list[dict[str, Any]] | None = None,
    heading: str | None = None,
    intro: str | None = None,
) -> str:
    """
    Founder intelligence feed: up to 5 items, image when available, no emojis or insights.
    """
    _ = intro

    chunks: list[dict[str, Any]] = []

    if top is not None or other is not None:
        chunks = list(top or []) + list(other or [])
    elif isinstance(news, dict) and ("top" in news or "other" in news):
        chunks = list(news.get("top") or []) + list(news.get("other") or [])
    elif isinstance(news, list):
        chunks = list(news)

    feed_items = chunks[:MAX_FEED_ITEMS]

    if heading is None:
        heading = "Founder Intelligence"

    h_esc = escape(str(heading).strip())
    tag_esc = escape(_TAGLINE)

    _ = tag_esc
    return build_feed_html(feed_items, title=h_esc)


def build_grouped_html(
    grouped_news: list[dict[str, Any]],
    *,
    heading: str,
    intro: str,
) -> str:
    _ = intro

    # Normalize legacy grouped shape to simple items (title/source/link).
    normalized: list[dict[str, Any]] = []
    for it in grouped_news:
        if not isinstance(it, dict):
            continue
        link = ""
        source = it.get("source") or ""
        if isinstance(it.get("sources"), list) and it["sources"]:
            s0 = it["sources"][0]
            if isinstance(s0, dict):
                source = s0.get("source") or source
                link = s0.get("link") or link
        link = it.get("link") or link
        normalized.append({"title": it.get("title") or "", "source": source, "link": link})

    return build_feed_html(normalized, title=heading)


def send_email(news: list[dict[str, Any]], subject: str, recipients: list[str], *, html: str | None = None) -> None:
    if _dev_mode_enabled():
        recipients = [DEV_EMAIL]

    if html is None:
        html = build_feed_html(news, title=subject)

    _send_html(subject, html, recipients)


def test_email() -> None:
    send_email(
        [
            {
                "title": "Test News",
                "sources": [{"source": "Test", "link": "http://test.com"}],
            }
        ],
        "Test Email",
        [os.getenv("TEST_EMAIL_RECIPIENT", DEV_EMAIL)],
    )


def send_report():
    today = datetime.now().date()
    json_path = f"reports/funding_report_{today}.json"

    if not os.path.exists(json_path):
        print("News report not found.")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        news = json.load(f)

    recipients = [DEV_EMAIL] if _dev_mode_enabled() else FOUNDER_EMAILS
    print("Sending email to:", recipients)

    html = build_edtech_html(news)
    subject = f"EdTech News – India ({today})"
    _send_html(subject, html, recipients)
    print("EdTech news email sent successfully.")


if __name__ == "__main__":
    send_report()
