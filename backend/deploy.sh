#!/usr/bin/env bash
# Full redeploy: build the frontend, install backend deps, restart gunicorn.
#   1. npm install + build the frontend (so app.py has something to serve)
#   2. pip install -r requirements.txt (into backend/.venv if present)
#   3. stop_gunicorn.sh (ignore "nothing to stop")
#   4. run_gunicorn.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "==> Building frontend"
npm --prefix ../frontend install
npm --prefix ../frontend run build

echo "==> Installing backend requirements"
if [[ -f .venv/bin/activate ]]; then
    # shellcheck disable=SC1091
    source .venv/bin/activate
fi
pip install -r requirements.txt

echo "==> Stopping existing app (if running)"
./stop_gunicorn.sh || true

echo "==> Starting app"
./run_gunicorn.sh
