from __future__ import annotations

import logging
import os
from pathlib import Path


def get_logger(domain: str) -> logging.Logger:
    """
    Domain log file:
      logs/edtech.log
      logs/cloud.log
      logs/genai.log
    """
    domain_key = (domain or "app").strip().lower()
    # normalize names to requested filenames
    domain_key = {"cloud_devops": "cloud", "genai": "genai", "edtech": "edtech"}.get(domain_key, domain_key)

    logger_name = f"competition_tracker.{domain_key}"
    logger = logging.getLogger(logger_name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    logs_dir = Path("logs")
    logs_dir.mkdir(parents=True, exist_ok=True)

    log_path = logs_dir / f"{domain_key}.log"

    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(fmt)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(fmt)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    # Prevent duplicate logs if root configured elsewhere
    logger.propagate = False

    # Keep noisy libraries quiet
    os.environ.setdefault("PYTHONUNBUFFERED", "1")
    return logger

