#!/bin/bash
set -euo pipefail

cd /root/competition-tracker || exit 1
source venv/bin/activate
python runners/run_edtech.py >> logs/edtech.log 2>&1

