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
