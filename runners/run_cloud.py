from __future__ import annotations

import sys
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from domains.cloud_devops.tracker import run
from common.logger import get_logger


logger = get_logger("cloud_devops")


def main() -> None:
    recipients_env = os.getenv("CLOUD_RECIPIENTS")
    if not recipients_env:
        raise ValueError("CLOUD_RECIPIENTS not set in .env")

    recipients = [x.strip() for x in recipients_env.split(",") if x.strip()]
    if not recipients:
        raise ValueError("CLOUD_RECIPIENTS has no valid email addresses")

    try:
        run(recipients=recipients)
    except Exception as e:
        logger.exception("Cloud runner failed: %s", e)


if __name__ == "__main__":
    main()
