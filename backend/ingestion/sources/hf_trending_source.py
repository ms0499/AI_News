"""Hugging Face's live "trending models" — free, no API key.

This replaces the archived Open LLM Leaderboard (hf_leaderboard_source) as the
primary community signal. That leaderboard is frozen and full of obscure merges;
this endpoint reflects what the open-model community is actually excited about
*right now*, refreshed every ingestion run. Frontier closed models (GPT/Gemini/
Claude) still live on the Models page's live catalog — this is the open-weights
complement to that.
"""

import requests

SOURCE_KEY = "hf-trending"
API_URL = "https://huggingface.co/api/models"
TOP_N = 25


def _fetch_trending() -> list[dict]:
    resp = requests.get(
        API_URL,
        params={
            "sort": "trendingScore",
            "direction": "-1",
            "limit": 60,
            "filter": "text-generation",
        },
        headers={"User-Agent": "AI-News/1.0"},
        timeout=30,
    )
    resp.raise_for_status()
    rows = []
    for m in resp.json():
        model_id = m.get("id")
        if not model_id or m.get("gated"):
            continue
        rows.append(
            {
                "model_name": model_id,
                "organization": model_id.split("/", 1)[0] if "/" in model_id else None,
                "score": float(m.get("trendingScore") or 0),
            }
        )
        if len(rows) >= TOP_N:
            break
    return rows


def fetch_and_store(session) -> int:
    """Replace this source's rows with a fresh trending snapshot. Returns the
    number of rows written (0 if the upstream API couldn't be fetched)."""
    from models import LeaderboardEntry

    try:
        rows = _fetch_trending()
    except (requests.RequestException, ValueError):
        return 0

    session.query(LeaderboardEntry).filter_by(source=SOURCE_KEY).delete()
    for rank, row in enumerate(rows, start=1):
        session.add(
            LeaderboardEntry(
                source=SOURCE_KEY,
                rank=rank,
                model_name=row["model_name"],
                organization=row["organization"],
                score=row["score"],
            )
        )
    session.commit()
    return len(rows)
