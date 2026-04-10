from __future__ import annotations

import os
import re
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import gspread
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from oauth2client.service_account import ServiceAccountCredentials

from common.unsubscribe_token import generate_token

CREDENTIALS_FILE = _PROJECT_ROOT / "credentials.json"
SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "1kUNV2PZvqT_x4YLvFQB0r1DqmQBWMm9zwl7fNnl_TeA")

_SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]

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


def _open_sheet():
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        str(CREDENTIALS_FILE),
        _SCOPE,
    )
    client = gspread.authorize(creds)
    return client.open_by_key(SHEET_ID).sheet1


def _header_indices(header_row: list[str]) -> tuple[int | None, int | None]:
    lowered = [str(h).strip().lower() for h in header_row]
    email_idx: int | None = None
    active_idx: int | None = None
    for i, name in enumerate(lowered):
        if name == "email":
            email_idx = i
        elif name == "active":
            active_idx = i
    return email_idx, active_idx


@app.get("/unsubscribe", response_class=HTMLResponse)
def unsubscribe(token: str | None = Query(default=None)) -> HTMLResponse:
    token_clean = str(token).strip().lower() if token is not None else ""
    if not token_clean or not re.fullmatch(r"[a-f0-9]{64}", token_clean):
        print("[UNSUBSCRIBE] invalid token format")
        return HTMLResponse(
            """
    <div style="font-family:Arial;text-align:center;margin-top:80px;">
        <h2>Invalid link</h2>
        <p>This unsubscribe link is invalid.</p>
    </div>
    """,
            status_code=400,
        )

    print(f"[UNSUBSCRIBE] token: {token_clean[:8]}...")

    try:
        sheet = _open_sheet()
    except Exception as e:
        print(f"[UNSUBSCRIBE] sheet error: {e}")
        return HTMLResponse(
            _html_page(
                "Unsubscribe",
                "We could not reach the subscriber list. Please try again later.",
            ),
            status_code=500,
        )

    try:
        all_values = sheet.get_all_values()
    except Exception as e:
        print(f"[UNSUBSCRIBE] read error: {e}")
        return HTMLResponse(
            _html_page("Unsubscribe", "Could not read subscriber data."),
            status_code=500,
        )

    if len(all_values) < 2:
        return HTMLResponse(
            _html_page("Unsubscribe", "No subscriber list found."),
            status_code=404,
        )

    header_row = all_values[0]
    email_col, active_col = _header_indices(header_row)

    if email_col is None:
        return HTMLResponse(
            _html_page("Unsubscribe", "Subscriber sheet is missing an Email column."),
            status_code=500,
        )
    if active_col is None:
        return HTMLResponse(
            _html_page("Unsubscribe", "Subscriber sheet is missing an Active column."),
            status_code=500,
        )

    found = False
    row_num: int | None = None
    for i, row in enumerate(all_values[1:], start=2):
        if email_col >= len(row):
            continue
        sheet_email = str(row[email_col]).strip()
        if not sheet_email or "@" not in sheet_email:
            continue
        if generate_token(sheet_email) == token_clean:
            found = True
            row_num = i
            print(f"[UNSUBSCRIBE] matched row {i}")
            break

    if not found:
        print("[UNSUBSCRIBE] not found")
        return HTMLResponse(
            """
    <div style="font-family:Arial;text-align:center;margin-top:80px;">
        <h2>Invalid link</h2>
        <p>This unsubscribe link is invalid or expired.</p>
    </div>
    """,
            status_code=404,
        )

    matched_row = all_values[row_num - 1]
    active_current = ""
    if active_col < len(matched_row):
        active_current = str(matched_row[active_col]).strip()

    try:
        if str(active_current).upper() != "FALSE":
            sheet.update_cell(row_num, active_col + 1, "FALSE")
            print("[UNSUBSCRIBE] sheet updated")
        else:
            print("[UNSUBSCRIBE] already inactive, skip sheet write")
    except Exception as e:
        print(f"[UNSUBSCRIBE] update error: {e}")
        return HTMLResponse(
            _html_page("Unsubscribe", "Could not update your subscription. Please try again later."),
            status_code=500,
        )

    print("[UNSUBSCRIBE] success")
    return HTMLResponse(
        """
<div style="font-family:Arial;text-align:center;margin-top:80px;">
  <h2>You've been unsubscribed</h2>
  <p>You will no longer receive these emails.</p>
</div>
""",
        status_code=200,
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
