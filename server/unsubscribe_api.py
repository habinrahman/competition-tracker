from __future__ import annotations

import re
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse

from common.logger import get_logger
from common.subscribers import unsubscribe_user
from common.unsubscribe_token import verify_token

logger = get_logger("unsubscribe")

app = FastAPI(title="Newsletter unsubscribe")


def _html_page(page_title: str, message: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{page_title}</title>
</head>
<body style="margin:0;font-family:Arial,sans-serif;background:#f5f5f5;">
  <div style="max-width:520px;margin:72px auto;padding:36px 28px;background:#fff;border-radius:10px;
              box-shadow:0 1px 4px rgba(0,0,0,.08);text-align:center;">
    <h1 style="font-size:22px;font-weight:600;margin:0 0 14px;color:#111;">{page_title}</h1>
    <p style="margin:0;color:#444;font-size:15px;line-height:1.55;">{message}</p>
  </div>
</body>
</html>"""


@app.get("/unsubscribe", response_class=HTMLResponse)
def unsubscribe(
    token: str | None = Query(default=None),
    type: str | None = Query(default=None),
) -> HTMLResponse:
    token_clean = str(token).strip().lower() if token is not None else ""
    if not token_clean or not re.fullmatch(r"[a-f0-9]{64}", token_clean):
        logger.warning("Invalid token format")
        return HTMLResponse(
            _html_page("Unsubscribe", "This unsubscribe link is invalid."),
            status_code=400,
        )

    type_clean = (str(type).strip().lower() if type is not None else "") or ""
    if type_clean not in ("cloud", "genai", "jobs", "all", "weekly"):
        logger.warning("Invalid or missing unsubscribe type=%s", type_clean)
        return HTMLResponse(
            _html_page(
                "Unsubscribe",
                "This unsubscribe link is missing a valid category.",
            ),
            status_code=400,
        )

    logger.info("Unsubscribe request token_prefix=%s type=%s", token_clean[:8], type_clean)

    try:
        email = verify_token(token_clean)
    except Exception:
        logger.exception("Token verification failed")
        return HTMLResponse(
            _html_page(
                "Unsubscribe",
                "We could not reach the subscriber list. Please try again later.",
            ),
            status_code=500,
        )

    if not email:
        logger.warning("No subscriber matched token")
        return HTMLResponse(
            _html_page(
                "Unsubscribe",
                "This unsubscribe link is invalid or no longer active.",
            ),
            status_code=404,
        )

    ok = unsubscribe_user(email, type_clean)
    if not ok:
        logger.warning("unsubscribe_user returned false email=%s type=%s", email, type_clean)
        return HTMLResponse(
            _html_page(
                "Unsubscribe",
                "We could not update your subscription. Please try again later.",
            ),
            status_code=404,
        )

    msg = "You have been unsubscribed from MicroDegree Weekly."

    logger.info("Unsubscribe completed email_suffix=%s type=%s", email.split("@")[-1], type_clean)
    return HTMLResponse(_html_page("Unsubscribe", msg), status_code=200)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
