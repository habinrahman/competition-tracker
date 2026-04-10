from __future__ import annotations

import os
import smtplib
import time
from collections.abc import Callable
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Amazon SES SMTP — set via env or replace defaults for local dev only
SMTP_HOST = os.getenv("SES_SMTP_HOST", "email-smtp.ap-south-1.amazonaws.com")
SMTP_PORT = int(os.getenv("SES_SMTP_PORT", "587"))

SMTP_USERNAME = "AKIAXZ5NGE5C727FFNM5"
SMTP_PASSWORD = "BJZwdMpjrCefDV7B86GCIbtzWHdco1lh0yPefnQ6zyZJ"

FROM_EMAIL = "MicroDegree <tech@mdegree.in>"


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
) -> None:
    """
    Send one personalized HTML message per recipient (required for per-user unsubscribe links).
    ``build_html(recipient_email)`` returns full HTML for that user.
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
                body = build_html(to_addr)
                msg = MIMEMultipart()
                msg["From"] = FROM_EMAIL
                msg["To"] = to_addr
                msg["Subject"] = subject
                msg.attach(MIMEText(body, "html"))

                server.sendmail(envelope_from, [to_addr], msg.as_string())

                if i % 50 == 0:
                    print(f"[MASS] sent {i}/{total}")

                time.sleep(0.2)  # ~5/s to reduce SES throttling

            except Exception as e:
                print(f"[ERROR] recipient {i} ({to_addr}): {e}")

    finally:
        server.quit()
