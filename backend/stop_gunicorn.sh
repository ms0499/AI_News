#!/usr/bin/env bash
# Stops the gunicorn master started by run_gunicorn.sh (reads logs/gunicorn.pid).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PIDFILE="logs/gunicorn.pid"

if [[ ! -f "$PIDFILE" ]]; then
    echo "No $PIDFILE found — is it running? (nothing to stop)"
    exit 1
fi

PID="$(cat "$PIDFILE")"
if ! kill -0 "$PID" 2>/dev/null; then
    echo "PID $PID (from $PIDFILE) isn't running. Removing stale pidfile."
    rm -f "$PIDFILE"
    exit 1
fi

kill -TERM "$PID"
echo "Sent stop signal to PID $PID."
