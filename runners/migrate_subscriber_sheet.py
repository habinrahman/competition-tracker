from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from common.subscribers import migrate_sheet_remove_legacy_categories


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Remove Cloud / GenAI / Jobs columns; keep Name, Email, Active only."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without editing the sheet.",
    )
    args = parser.parse_args()

    migrate_sheet_remove_legacy_categories(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
