"""Re-run the rule-based classifier (ingestion/classify.py) over every
existing article and update its section/companies/models/topics in place.

Ingestion only classifies an article once, at insert time — a keyword added
to classify.py later (e.g. a new model name, or a missing launch-announcement
verb like "introducing") never gets applied to articles that were already
ingested, since dedup skips any URL already in the database. This script
closes that gap without re-fetching anything.

Also re-runs record_model_release for any article that newly qualifies as a
"models" section article with a real model+company, so model_releases picks
up releases the original (stale) keyword lists missed.

Never touches ai_summary — this is the rule-based pass only.

Run with `python -m scripts.reclassify_articles` against whichever DB the
app is pointed at.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ingestion.classify import classify  # noqa: E402
from ingestion.run_ingestion import record_model_release  # noqa: E402
from models import Article, Source  # noqa: E402
from services.companies import get_or_create_company  # noqa: E402
from services.db import get_session  # noqa: E402


def run() -> None:
    session = get_session()
    try:
        changed = releases_recorded = 0
        sources = {s.id: s.name for s in session.query(Source).all()}

        for article in session.query(Article).all():
            tags = classify(article.title, article.raw_summary or "", sources.get(article.source_id))
            before = (article.section, article.companies or [], article.models or [], article.topics or [])
            after = (tags["section"], tags["companies"], tags["models"], tags["topics"])
            if before == after:
                continue

            article.section, article.companies, article.models, article.topics = after
            changed += 1

            for company_name in article.companies:
                get_or_create_company(session, company_name)

            if article.section == "models" and article.models and article.companies:
                record_model_release(session, article)
                releases_recorded += 1

        session.commit()
        print(f"Reclassified {changed} article(s), recorded/updated {releases_recorded} model release(s).")
    finally:
        session.close()


if __name__ == "__main__":
    run()
