"""Hugging Face's archived "Open LLM Leaderboard" (v2) dataset.

This is real, free, live data — but it's the archived leaderboard, ranking
community fine-tunes/merges of open-weight models. It never contains
frontier closed models (GPT/Gemini/Claude), so it's surfaced as a clearly
labeled secondary "community open-weights leaderboard," not the primary
"current best model" signal (that's the curated flagship flag in
data/curated_models.py).

Downloads the dataset's single ~1MB parquet file directly (via the public
datasets-server /parquet endpoint) rather than paging through thousands of
rows over the JSON /rows API — the rows aren't score-sorted, so getting a
true top-N requires the whole table anyway, and doing that as one small
file download is far gentler on the free public API than ~46 paginated
requests every run.
"""

import io

import pyarrow.parquet as pq
import requests

SOURCE_KEY = "hf-open-llm"
PARQUET_URL = (
    "https://huggingface.co/datasets/open-llm-leaderboard/contents/resolve/"
    "refs%2Fconvert%2Fparquet/default/train/0000.parquet"
)
TOP_N = 25


def _fetch_ranked_rows() -> list[dict]:
    resp = requests.get(PARQUET_URL, timeout=30)
    resp.raise_for_status()
    table = pq.read_table(io.BytesIO(resp.content), columns=["fullname", "Average ⬆️", "Flagged"])
    rows = [r for r in table.to_pylist() if not r.get("Flagged") and r.get("fullname")]
    rows.sort(key=lambda r: r["Average ⬆️"] or 0.0, reverse=True)
    return rows[:TOP_N]


def fetch_and_store(session) -> int:
    """Replaces this source's rows with a fresh top-N snapshot. Returns the
    number of rows written (0 if the upstream dataset couldn't be fetched)."""
    from models import LeaderboardEntry

    try:
        rows = _fetch_ranked_rows()
    except (requests.RequestException, OSError, ValueError):
        return 0

    session.query(LeaderboardEntry).filter_by(source=SOURCE_KEY).delete()
    for rank, row in enumerate(rows, start=1):
        fullname = row["fullname"]
        organization = fullname.split("/", 1)[0] if "/" in fullname else None
        session.add(
            LeaderboardEntry(
                source=SOURCE_KEY,
                rank=rank,
                model_name=fullname,
                organization=organization,
                score=row["Average ⬆️"],
            )
        )
    session.commit()
    return len(rows)
