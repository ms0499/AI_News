#!/usr/bin/env bash
# Production launch: serve app:app under gunicorn instead of Flask's dev server.
# Host-agnostic — same script for local prod-style testing and the NAS.
#
# Tuning (PORT, WEB_CONCURRENCY, GUNICORN_THREADS, ...) is read from .env by
# gunicorn.conf.py. Build the frontend first so app.py has something to serve:
#   npm --prefix ../frontend install && npm --prefix ../frontend run build
#
# Daemonizes (gunicorn's own --daemon, not shell backgrounding) so the shell
# prompt returns immediately. Access/error logs go to logs/ (see
# gunicorn.conf.py); the master's pid is written to logs/gunicorn.pid — use
# ./stop_gunicorn.sh to stop it.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [[ -f .venv/bin/activate ]]; then
    # shellcheck disable=SC1091
    source .venv/bin/activate
fi

mkdir -p logs

gunicorn -c gunicorn.conf.py --daemon --pid logs/gunicorn.pid app:app
echo "Started. PID: $(cat logs/gunicorn.pid). Logs in logs/. Stop with ./stop_gunicorn.sh"
