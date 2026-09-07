"""Gunicorn configuration for the AI News backend.

Loaded via:  gunicorn -c gunicorn.conf.py app:app  (see run_gunicorn.sh)

All tuning is env-driven and read from backend/.env — the same file app.py loads.
Knobs (all optional, with defaults):
  PORT (8010), WEB_CONCURRENCY (2), GUNICORN_THREADS (4),
  GUNICORN_WORKER_CLASS (gthread), GUNICORN_TIMEOUT (120),
  GUNICORN_GRACEFUL_TIMEOUT (30), GUNICORN_LOGLEVEL (info),
  GUNICORN_ACCESS_LOG (logs/gunicorn_access.log), GUNICORN_ERROR_LOG (logs/gunicorn_error.log).
  Set a log path to "-" to send that log to stdout/stderr (useful in a container).
"""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env", override=False)
except Exception:
    pass


def _int_env(name, default):
    try:
        val = (os.environ.get(name) or "").strip()
        return int(val) if val else default
    except (TypeError, ValueError):
        return default


bind = f"0.0.0.0:{_int_env('PORT', 8010)}"
workers = _int_env("WEB_CONCURRENCY", 2)
threads = _int_env("GUNICORN_THREADS", 4)
worker_class = (os.environ.get("GUNICORN_WORKER_CLASS") or "gthread").strip()
timeout = _int_env("GUNICORN_TIMEOUT", 120)
graceful_timeout = _int_env("GUNICORN_GRACEFUL_TIMEOUT", 30)
preload_app = False

loglevel = (os.environ.get("GUNICORN_LOGLEVEL") or "info").strip()
accesslog = (os.environ.get("GUNICORN_ACCESS_LOG") or "logs/gunicorn_access.log").strip()
errorlog = (os.environ.get("GUNICORN_ERROR_LOG") or "logs/gunicorn_error.log").strip()
capture_output = True
proc_name = "ai_news"
