from flask import Blueprint, jsonify

from config import Config
from models import BenchmarkScore
from services.db import get_session
from services.serialize import benchmark_score_to_dict

bp = Blueprint("benchmarks", __name__)


def _top(scores, key, reverse, limit=10):
    ranked = [s for s in scores if getattr(s, key) is not None]
    ranked.sort(key=lambda s: getattr(s, key), reverse=reverse)
    return [benchmark_score_to_dict(s) for s in ranked[:limit]]


@bp.get("/api/benchmarks")
def list_benchmarks():
    """Three top-10 leaderboards from one generated set: smartest (intelligence
    desc), fastest (speed desc), cheapest per task (cost asc)."""
    session = get_session()
    try:
        scores = session.query(BenchmarkScore).all()
        generated_at = max((s.generated_at for s in scores), default=None)
        source_note = scores[0].source_note if scores else None
        return jsonify(
            {
                "enabled": Config.BENCHMARK_ENABLED,
                "generated_at": generated_at.isoformat() if generated_at else None,
                "source_note": source_note,
                "intelligence": _top(scores, "intelligence", reverse=True),
                "speed": _top(scores, "speed", reverse=True),
                "cost": _top(scores, "cost", reverse=False),
            }
        )
    finally:
        session.close()
