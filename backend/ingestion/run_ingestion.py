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

from models import Article, IngestionRun, ModelRelease, Source  # noqa: E402
from services.ai_summarize import summarize_and_tag  # noqa: E402
from services.companies import get_or_create_company  # noqa: E402
from services.db import get_session, init_db  # noqa: E402
from services.dedup import normalize_url  # noqa: E402

from ingestion.classify import MODEL_TO_COMPANY, classify  # noqa: E402
from ingestion.sources import (  # noqa: E402
    hn_source,
    model_release_source,
    newsapi_source,
    reddit_source,
    rss_source,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

SOURCE_MODULES = [
    ("rss", rss_source),
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


def ingest_items(session, source_type: str, items: list[dict]) -> tuple[int, int]:
    found = len(items)
    new = 0
    for item in items:
        url = normalize_url(item["url"])
        if session.query(Article.id).filter_by(url=url).first():
            continue

        source = get_or_create_source(session, item["source_name"], source_type)
        tags = classify(item["title"], item.get("raw_summary", ""))
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
        release = (
            session.query(ModelRelease)
            .filter_by(company_id=company.id, model_name=model_name)
            .one_or_none()
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
    try:
        for source_type, module in SOURCE_MODULES:
            run_log = IngestionRun(source_id=None, status="running")
            session.add(run_log)
            session.commit()
            try:
                items = module.fetch_all()
                found, new = ingest_items(session, source_type, items)
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
    finally:
        session.close()


if __name__ == "__main__":
    run()
