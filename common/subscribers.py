from __future__ import annotations

import hmac
import os
import re
from datetime import datetime
from typing import Any

import gspread
from oauth2client.service_account import ServiceAccountCredentials

from common.logger import get_logger
from common.unsubscribe_token import generate_token as _unsubscribe_token

logger = get_logger("subscribers")

_DEFAULT_SHEET_ID = "1kUNV2PZvqT_x4YLvFQB0r1DqmQBWMm9zwl7fNnl_TeA"

_SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]

# Single subscription flag: Active = subscribed to MicroDegree Weekly.
_REQUIRED_ORDERED = ["Name", "Email", "Active", "Subscribed_On"]


def _open_sheet():
    credentials_file = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
    sheet_id = os.getenv("GOOGLE_SHEET_ID", _DEFAULT_SHEET_ID)

    creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, _SCOPE)
    client = gspread.authorize(creds)
    return client.open_by_key(sheet_id).sheet1


def ensure_columns(sheet) -> list[str]:
    """
    Ensure the subscriber sheet has: Name, Email, Active, Subscribed_On.
    Preserves existing header order; only appends missing columns.
    """
    header = sheet.row_values(1)
    header = [str(h).strip() for h in header]

    if not header:
        sheet.update("A1", [_REQUIRED_ORDERED])
        return list(_REQUIRED_ORDERED)

    seen = {c for c in header if c}
    merged = list(header)
    for col in _REQUIRED_ORDERED:
        if col not in seen:
            merged.append(col)
            seen.add(col)

    if merged != header:
        sheet.update("A1", [merged])
        logger.info("Subscriber sheet header extended: %s", merged)
        return merged

    return header


def _truthy(v: Any, *, default: bool = True) -> bool:
    if v is None:
        return default
    s = str(v).strip().lower()
    if s == "":
        return default
    return s in ("true", "1", "yes", "y", "on")


def _bool_to_cell(v: bool | str) -> str:
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    s = str(v).strip().lower()
    if s in ("false", "0", "no", "n", "off"):
        return "FALSE"
    return "TRUE"


def get_emails(category: str | None = None) -> list[str]:
    """
    Fetch active MicroDegree Weekly subscribers from Google Sheet.

    Only rows with ``Active`` TRUE are included. Legacy category columns
    (Cloud / GenAI / Jobs) are ignored if still present in the sheet.
    """
    if category:
        logger.warning(
            "get_emails(category=%r) is deprecated; using Active-only subscription.",
            category,
        )

    sheet = _open_sheet()
    ensure_columns(sheet)

    rows = sheet.get_all_records()
    if not rows:
        logger.info("No subscriber rows in sheet")
        return []

    if "Email" not in rows[0]:
        raise Exception("Missing 'Email' column in sheet")

    emails: list[str] = []
    for row in rows:
        email = str(row.get("Email", "")).strip()
        if not email or "@" not in email or "." not in email:
            continue

        if "Active" in row and not _truthy(row.get("Active"), default=True):
            continue

        emails.append(email)

    emails = list(dict.fromkeys(emails))
    logger.info("Active weekly subscribers: %d", len(emails))
    return emails


def add_subscriber(name: str, email: str) -> None:
    """
    Add or refresh a subscriber by email.

    Defaults: Active = TRUE; Subscribed_On = today.
    """
    sheet = _open_sheet()
    header = ensure_columns(sheet)

    email_clean = str(email or "").strip()
    if not email_clean or "@" not in email_clean:
        raise ValueError("Invalid email")

    name_clean = str(name or "").strip()
    today = datetime.now().strftime("%Y-%m-%d")

    all_values = sheet.get_all_values()
    if not all_values:
        sheet.update("A1", [header])
        all_values = [header]

    email_idx = header.index("Email")

    for i, row in enumerate(all_values[1:], start=2):
        existing = row[email_idx] if email_idx < len(row) else ""
        if str(existing).strip().lower() != email_clean.lower():
            continue

        updates: list[tuple[int, int, str]] = []
        if "Name" in header:
            ni = header.index("Name")
            cur = row[ni] if ni < len(row) else ""
            if name_clean and str(cur).strip() == "":
                updates.append((i, ni + 1, name_clean))

        if "Active" in header:
            ai = header.index("Active")
            current = row[ai] if ai < len(row) else ""
            if str(current).strip() == "":
                updates.append((i, ai + 1, "TRUE"))

        if "Subscribed_On" in header:
            si = header.index("Subscribed_On")
            cur_so = row[si] if si < len(row) else ""
            if str(cur_so).strip() == "":
                updates.append((i, si + 1, today))

        for r, c, v in updates:
            sheet.update_cell(r, c, v)
        logger.info("Updated existing subscriber row=%s email=%s", i, email_clean)
        return

    out_row = ["" for _ in header]
    if "Name" in header:
        out_row[header.index("Name")] = name_clean
    out_row[email_idx] = email_clean
    if "Active" in header:
        out_row[header.index("Active")] = "TRUE"
    if "Subscribed_On" in header:
        out_row[header.index("Subscribed_On")] = today

    sheet.append_row(out_row, value_input_option="RAW")
    logger.info("Appended new subscriber email=%s", email_clean)


def find_email_by_unsubscribe_token(token: str) -> str | None:
    """
    Return the sheet email address that matches a valid unsubscribe token, or None.
    """
    token_clean = str(token).strip().lower()
    if not re.fullmatch(r"[a-f0-9]{64}", token_clean):
        return None

    try:
        sheet = _open_sheet()
    except Exception:
        logger.exception("find_email_by_unsubscribe_token: could not open sheet")
        return None

    header = ensure_columns(sheet)
    try:
        all_values = sheet.get_all_values()
    except Exception:
        logger.exception("find_email_by_unsubscribe_token: could not read sheet")
        return None

    if len(all_values) < 2:
        return None

    lowered = [str(h).strip() for h in header]
    if "Email" not in lowered:
        return None

    email_col = lowered.index("Email")
    for row in all_values[1:]:
        if email_col >= len(row):
            continue
        sheet_email = str(row[email_col]).strip()
        if not sheet_email or "@" not in sheet_email:
            continue
        if hmac.compare_digest(_unsubscribe_token(sheet_email), token_clean):
            return sheet_email

    return None


def update_subscription(email: str, category: str, value: bool | str) -> None:
    """
    Set the ``Active`` subscription flag for one subscriber.

    Legacy category names (cloud, genai, jobs, weekly, all) map to ``Active``.
    """
    sheet = _open_sheet()
    header = ensure_columns(sheet)

    email_clean = str(email or "").strip()
    if not email_clean:
        raise ValueError("Invalid email")

    cat = str(category or "").strip().lower()
    allowed = {"active", "cloud", "genai", "jobs", "weekly", "all"}
    if cat not in allowed:
        raise ValueError(f"Unknown category: {category}")

    if "Active" not in header:
        raise ValueError("Sheet missing column: Active")

    all_values = sheet.get_all_values()
    if len(all_values) < 2:
        raise ValueError("No subscriber rows")

    email_idx = header.index("Email")
    col_idx = header.index("Active")
    cell_val = _bool_to_cell(value)

    for i, row in enumerate(all_values[1:], start=2):
        if email_idx >= len(row):
            continue
        if str(row[email_idx]).strip().lower() != email_clean.lower():
            continue
        sheet.update_cell(i, col_idx + 1, cell_val)
        logger.info(
            "Subscription updated email=%s column=Active value=%s",
            email_clean,
            cell_val,
        )
        return

    raise ValueError("Email not found in sheet")


def unsubscribe_user(email: str, category: str) -> bool:
    """
    Unsubscribe from MicroDegree Weekly by setting ``Active`` to FALSE.

    Any legacy category (cloud / genai / jobs / all / weekly) fully opts out.
    """
    cat = (category or "").strip().lower()
    if cat not in ("cloud", "genai", "jobs", "all", "weekly", "active"):
        logger.warning("unsubscribe_user: invalid category=%s", category)
        return False

    try:
        update_subscription(email, "active", False)
    except ValueError as e:
        logger.warning("unsubscribe_user failed: %s", e)
        return False
    except Exception:
        logger.exception("unsubscribe_user sheet error for email=%s", email)
        return False

    logger.info("unsubscribe_user ok email=%s category=%s", email, cat)
    return True
