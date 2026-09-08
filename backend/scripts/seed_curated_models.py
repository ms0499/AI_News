"""Populate `model_releases` with a hand-curated flagship-model list per
company (see data/curated_models.py), so the "AI Companies" widget has a
real "what's this model best for" answer even for companies the ingestion
pipeline hasn't covered with a real article yet.

Idempotent: safe to run repeatedly. Adds a row only if that company/model
pair doesn't already exist; only overwrites an existing row's description
when it's missing or is an unedited HF tag dump (see ENRICHED_DESCRIPTIONS).

Run with `python -m scripts.seed_curated_models` against whichever DB the
app is pointed at.
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data.curated_models import CURATED_MODELS, ENRICHED_DESCRIPTIONS, FLAGSHIP_MODELS  # noqa: E402
from models import Company, ModelRelease  # noqa: E402
from services.db import get_session  # noqa: E402


def _parse_date(value: str | None):
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone.utc)


def run() -> dict:
    session = get_session()
    inserted = enriched = skipped_no_company = flagged = 0
    try:
        for slug, models in CURATED_MODELS.items():
            company = session.query(Company).filter_by(slug=slug).one_or_none()
            if company is None:
                skipped_no_company += len(models)
                continue

            existing_names = {
                r.model_name.lower()
                for r in session.query(ModelRelease).filter_by(company_id=company.id).all()
            }
            for model in models:
                if model["model_name"].lower() in existing_names:
                    continue
                session.add(
                    ModelRelease(
                        company_id=company.id,
                        model_name=model["model_name"],
                        release_date=_parse_date(model["release_date"]),
                        description=model["description"],
                    )
                )
                inserted += 1

        for (slug, model_name), description in ENRICHED_DESCRIPTIONS.items():
            company = session.query(Company).filter_by(slug=slug).one_or_none()
            if company is None:
                continue
            release = (
                session.query(ModelRelease)
                .filter_by(company_id=company.id)
                .filter(ModelRelease.model_name.ilike(model_name))
                .one_or_none()
            )
            if release is None:
                continue
            if not release.description or release.description.startswith("Tags:"):
                release.description = description
                enriched += 1

        for slug, model_name in FLAGSHIP_MODELS.items():
            company = session.query(Company).filter_by(slug=slug).one_or_none()
            if company is None:
                continue
            releases = session.query(ModelRelease).filter_by(company_id=company.id).all()
            flagship = next((r for r in releases if r.model_name.lower() == model_name.lower()), None)
            if flagship is None:
                continue
            for release in releases:
                release.is_flagship = release.id == flagship.id
            flagged += 1

        session.commit()
        return {
            "inserted": inserted,
            "enriched": enriched,
            "skipped_no_company": skipped_no_company,
            "flagged": flagged,
        }
    finally:
        session.close()


if __name__ == "__main__":
    result = run()
    print(f"Inserted {result['inserted']} new model rows, enriched {result['enriched']} descriptions, "
          f"flagged {result['flagged']} flagship models "
          f"({result['skipped_no_company']} curated rows skipped — company slug not found).")
