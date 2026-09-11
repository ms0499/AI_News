from flask import Blueprint, jsonify, request

from config import Config
from models import BenchmarkScore, LeaderboardEntry
from services.db import get_session
from services.serialize import leaderboard_entry_to_dict

bp = Blueprint("leaderboard", __name__)

# Best-models-by-intelligence tabs, sourced from the Artificial Analysis
# scoreboard (see ingestion/sources/benchmark_source.py) rather than the
# hf-trending/hf-open-llm tables above.
_AA_SOURCES = {"aa-open": True, "aa-closed": False}


def _aa_leaderboard(is_open_weights: bool, limit: int = 20) -> list[dict]:
    session = get_session()
    try:
        scores = (
            session.query(BenchmarkScore)
            .filter(BenchmarkScore.is_open_weights == is_open_weights)
            .filter(BenchmarkScore.intelligence.isnot(None))
            .order_by(BenchmarkScore.intelligence.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "id": s.id,
                "rank": i + 1,
                "model_name": s.model_name,
                "organization": s.company,
                "score": s.intelligence,
                "fetched_at": s.generated_at.isoformat() if s.generated_at else None,
            }
            for i, s in enumerate(scores)
        ]
    finally:
        session.close()


@bp.get("/api/leaderboard")
def list_leaderboard():
    source = request.args.get("source", "hf-trending")

    if source in _AA_SOURCES:
        entries = _aa_leaderboard(_AA_SOURCES[source]) if Config.BENCHMARK_ENABLED else []
        return jsonify({"source": source, "entries": entries})

    session = get_session()
    try:
        entries = (
            session.query(LeaderboardEntry)
            .filter_by(source=source)
            .order_by(LeaderboardEntry.rank)
            .all()
        )
        return jsonify({"source": source, "entries": [leaderboard_entry_to_dict(e) for e in entries]})
    finally:
        session.close()
