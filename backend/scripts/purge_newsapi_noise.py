"""One-off cleanup for articles pulled in under the old, overly-broad NewsAPI
query (see ingestion/sources/newsapi_source.py) — full-text body search for
generic terms like "AI"/"LLM" surfaced sports recaps, PyPI package listings,
and tabloid stories that mentioned AI once, none of it from the reputable
outlets the new query/domain-restricted version targets.

Deletes every Article whose source is type "newsapi" and NOT in the current
allowlisted set of publication display names newsapi_source.py's DOMAINS
list actually maps to. As of this script's writing, that's every single
newsapi-sourced article in the database (verified: zero rows matched a
reputable outlet before this cleanup) — going forward, the tightened query
should only bring in ones that do.

Run with `python -m scripts.purge_newsapi_noise` against whichever DB the
app is pointed at. Safe to re-run; only ever deletes, never modifies.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from models import Article, Source  # noqa: E402
from services.db import get_session  # noqa: E402

# Display names NewsAPI actually returns for the outlets in newsapi_source.DOMAINS.
KEEP_PUBLICATIONS = {
    "TechCrunch",
    "The Verge",
    "Ars Technica",
    "Wired",
    "VentureBeat",
    "MIT Technology Review",
    "Reuters",
    "Bloomberg",
    "CNBC",
    "The Guardian",
    "Engadget",
    "Axios",
    "Business Insider",
    "Forbes",
}


def run() -> None:
    session = get_session()
    try:
        deleted = 0
        newsapi_sources = session.query(Source).filter_by(type="newsapi").all()
        for source in newsapi_sources:
            if source.name in KEEP_PUBLICATIONS:
                continue
            count = session.query(Article).filter_by(source_id=source.id).delete()
            deleted += count

        session.commit()
        print(f"Deleted {deleted} low-quality newsapi-sourced article(s).")
    finally:
        session.close()


if __name__ == "__main__":
    run()
