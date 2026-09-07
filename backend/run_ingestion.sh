#!/usr/bin/env bash
# Cron/Task Scheduler entry point for one ingestion pass. Point the scheduler at this
# script (every 15-30 min) rather than invoking python directly, so venv activation and
# the working directory are always correct regardless of the scheduler's own cwd/env.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [[ -f .venv/bin/activate ]]; then
    # shellcheck disable=SC1091
    source .venv/bin/activate
fi

mkdir -p logs
exec python -m ingestion.run_ingestion >> logs/ingestion.log 2>&1
