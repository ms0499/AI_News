"""One-off repair for ModelRelease rows created by the section-routing bug in
ingestion/classify.py: a research paper that merely used an existing model as
a benchmark baseline (nearly every ML abstract says "state-of-the-art") could
get classified as section="models" before its "research" topic ("arxiv" in
the text) had a chance to route it to "papers" instead — so models named as
baselines got recorded as fake releases, dated as of the ingestion run.

That routing bug is fixed (see classify.py's SECTION_PRIORITY), but the fix
doesn't retroactively touch rows already in the database. This re-runs the
now-fixed classify() against each release's source article and, wherever
that changes the section away from "models", deletes the release and
refreshes the article's section/companies/models/topics to match.

Hugging Face Models feed items are exempt: that source hardcodes
section="models" for its own reasons (see ingestion/sources/
model_release_source.py) and was never routed through classify()'s section
heuristic in the first place, so reclassifying them here would be wrong.

Run once with `python -m scripts.fix_fake_paper_releases` after pulling this
fix, against whichever DB the app is pointed at.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ingestion.classify import classify  # noqa: E402
from models import Article, ModelRelease, Source  # noqa: E402
from services.db import get_session  # noqa: E402

EXEMPT_SOURCE_NAMES = {"Hugging Face Models"}


def run() -> None:
    session = get_session()
    try:
        removed = 0
        for release in session.query(ModelRelease).all():
            if release.source_article_id is None:
                continue
            article = session.get(Article, release.source_article_id)
            if article is None:
                continue

            source_name = None
            if article.source_id is not None:
                source = session.get(Source, article.source_id)
                source_name = source.name if source else None
            if source_name in EXEMPT_SOURCE_NAMES:
                continue

            tags = classify(article.title, article.raw_summary or "")
            if tags["section"] == "models":
                continue

            print(f"removing release {release.id} ({release.model_name!r}) "
                  f"from article {article.id} ({article.title[:60]!r}) "
                  f"-> section {tags['section']!r}")
            session.delete(release)
            article.section = tags["section"]
            article.companies = tags["companies"]
            article.models = tags["models"]
            article.topics = tags["topics"]
            removed += 1

        session.commit()
        print(f"Removed {removed} fake release(s).")
    finally:
        session.close()


if __name__ == "__main__":
    run()
