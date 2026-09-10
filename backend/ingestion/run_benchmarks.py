"""Refreshes the "Model Benchmarks" scoreboard — a SEPARATE, ~daily job.

This is intentionally decoupled from run_ingestion (which runs hourly). The
benchmark scores come from a grounded LLM and barely move day-to-day, so
regenerating them every ingestion pass would burn grounded API requests for no
benefit. Schedule this on its own, roughly once a day:

    # crontab: 07:15 every day
    15 7 * * *  cd /path/to/backend && /path/to/python -m ingestion.run_benchmarks

A freshness guard (Config.BENCHMARK_MIN_INTERVAL_HOURS) makes this a no-op if
the table was refreshed more recently, so a misfiring or duplicate cron can't
burn requests. Pass --force to regenerate regardless.
"""

import argparse
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import Config  # noqa: E402
from models import BenchmarkScore  # noqa: E402
from services.db import get_session, init_db  # noqa: E402

from ingestion.sources import artificial_analysis, benchmark_source  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def _hours_since_last_refresh(session) -> float | None:
    """Age in hours of the most recent benchmark row, or None if the table is
    empty (nothing generated yet)."""
    latest = session.query(BenchmarkScore.generated_at).order_by(
        BenchmarkScore.generated_at.desc()
    ).first()
    if latest is None or latest[0] is None:
        return None
    generated_at = latest[0]
    if generated_at.tzinfo is None:  # stored naive -> treat as UTC
        generated_at = generated_at.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - generated_at).total_seconds() / 3600.0


def run(force: bool = False) -> None:
    # Prefer the Artificial Analysis API (real, independent numbers) whenever a
    # key is configured; otherwise fall back to the grounded-LLM generator.
    use_aa = bool(Config.AA_ENABLED and Config.AA_API_KEY)
    if not use_aa:
        if not Config.BENCHMARK_ENABLED:
            logger.info(
                "benchmark: no AA_API_KEY and BENCHMARK_ENABLED is false — nothing to do"
            )
            return
        if not Config.BENCHMARK_API_KEY:
            logger.warning("benchmark: no AA key and no LLM key configured — skipping")
            return

    init_db()
    session = get_session()
    try:
        if not force:
            age = _hours_since_last_refresh(session)
            min_interval = Config.BENCHMARK_MIN_INTERVAL_HOURS
            if age is not None and age < min_interval:
                logger.info(
                    "benchmark: last refresh was %.1fh ago (< %.1fh) — skipping. "
                    "Use --force to override.",
                    age,
                    min_interval,
                )
                return

        source = "Artificial Analysis" if use_aa else "grounded LLM"
        logger.info("benchmark: refreshing scoreboard via %s", source)
        if use_aa:
            n = artificial_analysis.fetch_and_store(session)
        else:
            n = benchmark_source.fetch_and_store(session)
        if n:
            logger.info("benchmark: wrote %d rows", n)
        else:
            # fetch_and_store returns 0 on any failure and leaves old rows intact.
            logger.warning(
                "benchmark: no rows written — generation failed or returned "
                "nothing; previous scoreboard left in place"
            )
    except Exception:
        session.rollback()
        logger.exception("benchmark refresh failed")
    finally:
        session.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Refresh the Model Benchmarks scoreboard")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate even if refreshed within BENCHMARK_MIN_INTERVAL_HOURS",
    )
    args = parser.parse_args()
    run(force=args.force)
