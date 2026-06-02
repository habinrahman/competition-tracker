from __future__ import annotations

import os
import smtplib
import time
from collections.abc import Callable
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from common.emailer import build_unsubscribe_url

# Amazon SES SMTP — set via env or replace defaults for local dev only
SMTP_HOST = os.getenv("SES_SMTP_HOST", "email-smtp.ap-south-1.amazonaws.com")
SMTP_PORT = int(os.getenv("SES_SMTP_PORT", "587"))

SMTP_USERNAME = "AKIAXZ5NGE5C727FFNM5"
SMTP_PASSWORD = "BJZwdMpjrCefDV7B86GCIbtzWHdco1lh0yPefnQ6zyZJ"

FROM_EMAIL = "MicroDegree <tech@mdegree.in>"
REPLY_TO = os.getenv("NEWSLETTER_REPLY_TO", "tech@mdegree.in").strip()


def _envelope_sender(from_header: str) -> str:
    """SES envelope/from must be a bare address if header is Name <addr>."""
    h = (from_header or "").strip()
    if "<" in h and ">" in h:
        return h.split("<", 1)[1].split(">", 1)[0].strip()
    return h


def send_bulk(
    emails: list[str],
    subject: str,
    *,
    build_html: Callable[[str], str],
    build_plain: Callable[[str], str] | None = None,
) -> None:
    """
    Send one personalized HTML message per recipient (required for per-user unsubscribe links).
    ``build_html(recipient_email)`` returns full HTML for that user.
    Optional ``build_plain`` adds a text/plain part (better inbox placement).
    """

    envelope_from = _envelope_sender(FROM_EMAIL)
    total = len(emails)
    print(f"[MASS] Total users: {total}")

    server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
    try:
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)

        for i, to_addr in enumerate(emails):
            to_addr = (to_addr or "").strip()
            if not to_addr or "@" not in to_addr:
                print(f"[MASS] skip invalid address at index {i}")
                continue

            try:
                html_body = build_html(to_addr)
                unsub_url = build_unsubscribe_url(to_addr, "all")

                msg = MIMEMultipart("alternative")
                msg["From"] = FROM_EMAIL
                msg["To"] = to_addr
                msg["Subject"] = subject
                if REPLY_TO:
                    msg["Reply-To"] = REPLY_TO
                msg["List-Unsubscribe"] = f"<{unsub_url}>"
                msg["List-Unsubscribe-Post"] = "List-Unsubscribe=One-Click"

                if build_plain is not None:
                    msg.attach(MIMEText(build_plain(to_addr), "plain", "utf-8"))
                else:
                    msg.attach(
                        MIMEText(
                            f"MicroDegree Weekly\n\nUnsubscribe: {unsub_url}",
                            "plain",
                            "utf-8",
                        )
                    )
                msg.attach(MIMEText(html_body, "html", "utf-8"))

                server.sendmail(envelope_from, [to_addr], msg.as_string())

                if i % 50 == 0:
                    print(f"[MASS] sent {i}/{total}")

                time.sleep(0.2)  # ~5/s to reduce SES throttling

            except Exception as e:
                print(f"[ERROR] recipient {i} ({to_addr}): {e}")

    finally:
        server.quit()
