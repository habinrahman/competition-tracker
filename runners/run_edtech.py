from __future__ import annotations

import sys
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from domains.edtech.tracker import run
from common.logger import get_logger


logger = get_logger("edtech")


def main() -> None:
    recipients_env = os.getenv("EDTECH_RECIPIENTS")
    if not recipients_env:
        raise ValueError("EDTECH_RECIPIENTS not set in .env")

    recipients = [x.strip() for x in recipients_env.split(",") if x.strip()]
    if not recipients:
        raise ValueError("EDTECH_RECIPIENTS has no valid email addresses")
    try:
        run(recipients=recipients)
    except Exception as e:
        logger.exception("EdTech runner failed: %s", e)


if __name__ == "__main__":
    main()

