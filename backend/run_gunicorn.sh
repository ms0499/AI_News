#!/usr/bin/env bash
# Production launch: serve app:app under gunicorn instead of Flask's dev server.
# Host-agnostic — same script for local prod-style testing and the NAS.
#
# Tuning (PORT, WEB_CONCURRENCY, GUNICORN_THREADS, ...) is read from .env by
# gunicorn.conf.py. Build the frontend first so app.py has something to serve:
#   npm --prefix ../frontend install && npm --prefix ../frontend run build
#
# Runs in the foreground (exec) so it works under a supervisor / systemd / cron @reboot.
# To run detached: nohup ./run_gunicorn.sh > logs/gunicorn.out 2>&1 &
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [[ -f .venv/bin/activate ]]; then
    # shellcheck disable=SC1091
    source .venv/bin/activate
fi

mkdir -p logs

exec gunicorn -c gunicorn.conf.py app:app
