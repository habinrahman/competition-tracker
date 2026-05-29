from __future__ import annotations

from dotenv import load_dotenv
load_dotenv()

import hashlib
import hmac
import os

SECRET = os.getenv("UNSUBSCRIBE_SECRET")

if not SECRET:
    raise Exception("UNSUBSCRIBE_SECRET not set")


def generate_token(email: str) -> str:
    normalized = str(email).strip().lower().encode()
    return hmac.new(SECRET.encode(), normalized, hashlib.sha256).hexdigest()


def verify_token(token: str) -> str | None:
    """Return the subscriber email for a valid token, else None (lazy import avoids cycles)."""
    from common.subscribers import find_email_by_unsubscribe_token

    return find_email_by_unsubscribe_token(token)
