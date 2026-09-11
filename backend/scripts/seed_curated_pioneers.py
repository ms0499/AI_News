"""Populate `pioneers` from the hand-curated list in data/curated_pioneers.py.

Idempotent: inserts by `slug`, skips ones that already exist so re-running
(e.g. from the admin route) never duplicates rows. Edits to an existing
entry's bio/role/etc. in curated_pioneers.py are picked up by re-running
this — existing rows are updated in place, not just skipped.

Run with `python -m scripts.seed_curated_pioneers` against whichever DB the
app is pointed at.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data.curated_pioneers import CURATED_PIONEERS  # noqa: E402
from models import Pioneer  # noqa: E402
from services.db import get_session  # noqa: E402


def run() -> dict:
    session = get_session()
    inserted = updated = 0
    try:
        for sort_order, entry in enumerate(CURATED_PIONEERS):
            pioneer = session.query(Pioneer).filter_by(slug=entry["slug"]).one_or_none()
            fields = {
                "name": entry["name"],
                "role": entry.get("role"),
                "company_name": entry.get("company_name"),
                "contribution": entry.get("contribution"),
                "bio": entry.get("bio"),
                "photo_url": entry.get("photo_url"),
                "links": entry.get("links", []),
                "sort_order": sort_order,
                "latest_quote": entry.get("latest_quote"),
                "quote_date": entry.get("quote_date"),
                "quote_source_label": entry.get("quote_source_label"),
                "quote_source_url": entry.get("quote_source_url"),
            }
            if pioneer is None:
                session.add(Pioneer(slug=entry["slug"], **fields))
                inserted += 1
            else:
                for key, value in fields.items():
                    setattr(pioneer, key, value)
                updated += 1

        session.commit()
        return {"inserted": inserted, "updated": updated}
    finally:
        session.close()


if __name__ == "__main__":
    result = run()
    print(f"Inserted {result['inserted']} new pioneers, updated {result['updated']} existing.")
