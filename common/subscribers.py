from __future__ import annotations

import gspread
from oauth2client.service_account import ServiceAccountCredentials


def get_emails():
    """
    Fetch ONLY active emails from Google Sheet
    """

    CREDENTIALS_FILE = "credentials.json"
    SHEET_ID = "1kUNV2PZvqT_x4YLvFQB0r1DqmQBWMm9zwl7fNnl_TeA"

    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]

    creds = ServiceAccountCredentials.from_json_keyfile_name(
        CREDENTIALS_FILE,
        scope,
    )

    client = gspread.authorize(creds)

    sheet = client.open_by_key(SHEET_ID).sheet1

    rows = sheet.get_all_records()

    if not rows:
        print("[SUBSCRIBERS] No data found")
        return []

    # Safety check
    if "Email" not in rows[0]:
        raise Exception("Missing 'Email' column in sheet")

    if "Active" not in rows[0]:
        print("[WARN] 'Active' column missing, defaulting all to TRUE")

    emails = []

    for row in rows:
        email = str(row.get("Email", "")).strip()
        active = str(row.get("Active", "TRUE")).strip().lower()

        if email and active in ["true", "1", "yes"] and "@" in email and "." in email:
            emails.append(email)

    # Deduplicate without breaking order
    emails = list(dict.fromkeys(emails))

    print(f"[SUBSCRIBERS] Active users: {len(emails)}")

    return emails