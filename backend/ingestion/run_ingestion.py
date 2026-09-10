"""Orchestrates one ingestion pass: fetch every source -> dedup -> classify
-> optional AI summarize -> upsert into Postgres, logging one ingestion_runs
row per source so failures are visible without digging through logs.

Run manually with `python -m ingestion.run_ingestion`, or on a schedule
(NAS cron/launchd) every 15-30 minutes.
"""

import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import Config  # noqa: E402
from models import Article, IngestionRun, ModelRelease, Source  # noqa: E402
from services.ai_summarize import summarize_and_tag  # noqa: E402
from services.companies import get_or_create_company  # noqa: E402
from services.db import get_session, init_db  # noqa: E402
from services.dedup import normalize_url  # noqa: E402

from ingestion.classify import MODEL_TO_COMPANY, classify  # noqa: E402
from ingestion.sources import (  # noqa: E402
    funding_source,
    hf_leaderboard_source,
    hf_trending_source,
    hn_source,
    model_release_source,
    newsapi_source,
    openrouter_models,
    reddit_source,
    rss_source,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

SOURCE_MODULES = [
    ("rss", rss_source),
    ("funding", funding_source),
    ("hn", hn_source),
    ("reddit", reddit_source),
    ("newsapi", newsapi_source),
    ("hf", model_release_source),
]


def get_or_create_source(session, name: str, source_type: str) -> Source:
    source = session.query(Source).filter_by(name=name).one_or_none()
    if source is None:
        source = Source(name=name, type=source_type, url="", category=source_type)
        session.add(source)
        session.flush()
    return source


def ingest_items(
    session, source_type: str, items: list[dict], ai_budget: list[int] | None = None
) -> tuple[int, int]:
    found = len(items)
    new = 0
    for item in items:
        url = normalize_url(item["url"])
        if session.query(Article.id).filter_by(url=url).first():
            continue

        source = get_or_create_source(session, item["source_name"], source_type)
        tags = classify(item["title"], item.get("raw_summary", ""), item["source_name"])
        # Summarize only while this run still has AI budget left. Past the cap,
        # ai_result stays None and the article keeps its raw summary — so a large
        # backlog degrades gracefully instead of exhausting the daily quota.
        # The budget counts every attempt (not just successes): if the API is
        # erroring or rate-limited it returns None, and we must not keep hammering
        # it for every remaining article — the cap is a hard ceiling on calls.
        ai_result = None
        if ai_budget is None or ai_budget[0] > 0:
            if ai_budget is not None:
                ai_budget[0] -= 1
            ai_result = summarize_and_tag(item["title"], item.get("raw_summary", ""))

        article = Article(
            source_id=source.id,
            title=item["title"],
            url=url,
            author=item.get("author"),
            published_at=item.get("published_at"),
            raw_summary=item.get("raw_summary"),
            ai_summary=(ai_result or {}).get("summary"),
            image_url=item.get("image_url"),
            section=item.get("section") or tags["section"],
            companies=(ai_result or {}).get("companies") or tags["companies"],
            models=(ai_result or {}).get("models") or tags["models"],
            topics=(ai_result or {}).get("topics") or tags["topics"],
        )
        session.add(article)
        session.flush()

        for company_name in article.companies or []:
            get_or_create_company(session, company_name)

        if article.section == "models" and article.models and article.companies:
            record_model_release(session, article)

        new += 1
    session.commit()
    return found, new


def record_model_release(session, article: Article) -> None:
    """One release row per (company, model) pair mentioned in a models-section
    article — later articles about the same model just update the description/
    date rather than piling up duplicate rows.

    Each model is attributed to its actual maker via MODEL_TO_COMPANY, not to
    whichever company the article happens to mention first — a comparison
    article ("OpenAI reacts to Google's Gemini 3") would otherwise attribute
    Gemini 3 to OpenAI.
    """
    for model_name in article.models:
        company_name = MODEL_TO_COMPANY.get(model_name.lower(), article.companies[0])
        company = get_or_create_company(session, company_name)
        # Only match/create article-derived rows (catalog_key IS NULL). Catalog
        # rows from the OpenRouter source are authoritative and must not be
        # clobbered here — and a shared model_name across a catalog row and an
        # article row would otherwise make one_or_none() raise MultipleResults.
        release = (
            session.query(ModelRelease)
            .filter(
                ModelRelease.company_id == company.id,
                ModelRelease.model_name == model_name,
                ModelRelease.catalog_key.is_(None),
            )
            .first()
        )
        if release is None:
            release = ModelRelease(company_id=company.id, model_name=model_name)
            session.add(release)
        release.release_date = article.published_at or release.release_date
        release.description = article.ai_summary or article.raw_summary or release.description
        release.source_article_id = article.id


def run() -> None:
    init_db()
    session = get_session()
    # Run-wide AI summarize budget, shared across every source module so the cap
    # is per ingestion pass (not per source). Mutable single-element list so
    # ingest_items can decrement it in place. None = unlimited (feature off).
    ai_budget = None
    if Config.AI_SUMMARIZE_ENABLED:
        ai_budget = [Config.AI_SUMMARIZE_MAX_PER_RUN]
    try:
        for source_type, module in SOURCE_MODULES:
            run_log = IngestionRun(source_id=None, status="running")
            session.add(run_log)
            session.commit()
            try:
                items = module.fetch_all()
                found, new = ingest_items(session, source_type, items, ai_budget)
                run_log.status = "ok"
                run_log.items_found = found
                run_log.items_new = new
                logger.info("%s: found=%d new=%d", source_type, found, new)
            except Exception as exc:  # keep going even if one source fails
                session.rollback()
                run_log = session.merge(run_log)
                run_log.status = "error"
                run_log.error = str(exc)
                logger.exception("%s ingestion failed", source_type)

            run_log.finished_at = datetime.now(timezone.utc)
            session.commit()

        if ai_budget is not None:
            used = Config.AI_SUMMARIZE_MAX_PER_RUN - ai_budget[0]
            logger.info(
                "ai_summarize: used %d/%d calls%s",
                used,
                Config.AI_SUMMARIZE_MAX_PER_RUN,
                " (cap reached — remaining articles kept raw summaries)"
                if ai_budget[0] == 0
                else "",
            )

        try:
            n = openrouter_models.fetch_and_store(session)
            logger.info("openrouter_models: upserted %d catalog rows", n)
        except Exception:  # catalog refresh, never let it break the main pass
            session.rollback()
            logger.exception("openrouter_models refresh failed")

        try:
            n = hf_trending_source.fetch_and_store(session)
            logger.info("hf_trending: wrote %d rows", n)
        except Exception:  # separate table, never let this break the main pass
            session.rollback()
            logger.exception("hf_trending refresh failed")

        try:
            n = hf_leaderboard_source.fetch_and_store(session)
            logger.info("hf_leaderboard: wrote %d rows", n)
        except Exception:  # separate table, never let this break the main pass
            session.rollback()
            logger.exception("hf_leaderboard refresh failed")

        # NOTE: the Model Benchmarks scoreboard is deliberately NOT refreshed here.
        # It uses a grounded LLM whose standings barely move day-to-day, so it runs
        # from its own entrypoint (ingestion.run_benchmarks) on a ~daily schedule
        # instead of every hourly ingestion pass — see run_benchmarks.py.
    finally:
        session.close()


if __name__ == "__main__":
    run()
