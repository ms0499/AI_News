"""One-off repair for ModelRelease rows that ended up duplicated by casing
alone (e.g. "Gpt-5" and "GPT-5" as separate rows for the same company) —
happens when classify.py's display-name casing for a model keyword changes
(see MODEL_DISPLAY_NAMES) and record_model_release's exact-name lookup no
longer matches the old row, so a fresh one gets created instead of updating it.

Keeps one row per (company, model_name.lower()): prefers the one already
flagged is_flagship, then the one with a real (non-empty) description, then
the most recently touched row; merges release_date/description/flagship onto
the survivor before deleting the rest.

Run with `python -m scripts.merge_duplicate_model_releases` against whichever
DB the app is pointed at.
"""

import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from models import ModelRelease  # noqa: E402
from services.db import get_session  # noqa: E402


def _rank(release: ModelRelease) -> tuple:
    return (release.is_flagship, bool(release.description), release.id)


def run() -> None:
    session = get_session()
    try:
        groups: dict[tuple, list[ModelRelease]] = defaultdict(list)
        for release in session.query(ModelRelease).all():
            groups[(release.company_id, release.model_name.lower())].append(release)

        merged = 0
        for releases in groups.values():
            if len(releases) < 2:
                continue
            releases.sort(key=_rank, reverse=True)
            survivor, dupes = releases[0], releases[1:]
            for dupe in dupes:
                if dupe.is_flagship:
                    survivor.is_flagship = True
                if dupe.release_date and not survivor.release_date:
                    survivor.release_date = dupe.release_date
                if dupe.description and not survivor.description:
                    survivor.description = dupe.description
                session.delete(dupe)
                merged += 1

        session.commit()
        print(f"Merged {merged} duplicate model_release row(s).")
    finally:
        session.close()


if __name__ == "__main__":
    run()
