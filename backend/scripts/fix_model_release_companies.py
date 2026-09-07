"""One-off repair for ModelRelease rows created before the maker-attribution
fix in ingestion/run_ingestion.py::record_model_release. That code used to
attribute every model in an article to article.companies[0], so a model could
end up filed under the wrong company (e.g. Gemini 3 under OpenAI, in an
article that mentioned OpenAI first). This reassigns each existing release to
its real maker via classify.MODEL_TO_COMPANY, merging into an existing row
for the correct company when one already exists.

Run once with `python -m scripts.fix_model_release_companies` after pulling
the fix, against whichever DB the app is pointed at.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ingestion.classify import MODEL_TO_COMPANY  # noqa: E402
from models import ModelRelease  # noqa: E402
from services.companies import get_or_create_company  # noqa: E402
from services.db import get_session  # noqa: E402


def run() -> None:
    session = get_session()
    try:
        moved = merged = 0
        for release in session.query(ModelRelease).all():
            correct_name = MODEL_TO_COMPANY.get(release.model_name.lower())
            if not correct_name:
                continue
            correct_company = get_or_create_company(session, correct_name)
            if release.company_id == correct_company.id:
                continue

            existing = (
                session.query(ModelRelease)
                .filter_by(company_id=correct_company.id, model_name=release.model_name)
                .one_or_none()
            )
            if existing is None:
                release.company_id = correct_company.id
                moved += 1
            else:
                if (release.release_date or None) and not existing.release_date:
                    existing.release_date = release.release_date
                if release.description and not existing.description:
                    existing.description = release.description
                session.delete(release)
                merged += 1

        session.commit()
        print(f"Reassigned {moved} release(s), merged {merged} duplicate(s).")
    finally:
        session.close()


if __name__ == "__main__":
    run()
