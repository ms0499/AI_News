from flask import Blueprint, jsonify, request

from config import Config
from models import BenchmarkScore
from services.db import get_session
from services.serialize import benchmark_score_to_dict

bp = Blueprint("benchmarks", __name__)

# Cost ranks every scored model ascending by price, so left unfiltered the
# cheapest slots go to obscure/niche providers rather than the well-known labs
# people actually compare prices across. Restrict the cost category to this
# curated set of major labs before ranking.
_FAMOUS_COMPANIES = {
    "openai", "anthropic", "google", "google deepmind", "meta", "meta ai",
    "xai", "deepseek", "alibaba", "qwen", "mistral", "mistral ai",
    "microsoft", "amazon", "moonshot ai", "moonshot",
}


def _is_famous(score) -> bool:
    return (score.company or "").strip().lower() in _FAMOUS_COMPANIES


def _top(scores, key, reverse, limit=10, balanced=False, famous_only=False):
    ranked = [s for s in scores if getattr(s, key) is not None]
    if famous_only:
        ranked = [s for s in ranked if _is_famous(s)]
    if not balanced:
        ranked.sort(key=lambda s: getattr(s, key), reverse=reverse)
        return [benchmark_score_to_dict(s) for s in ranked[:limit]]

    # Rank open-weight and closed models separately, then take up to half the
    # limit from each and re-merge — so a flat sort (which closed frontier
    # models tend to dominate on intelligence) can't crowd open models out.
    limit_each = max(1, limit // 2)
    open_ranked = sorted(
        (s for s in ranked if s.is_open_weights is True),
        key=lambda s: getattr(s, key),
        reverse=reverse,
    )
    closed_ranked = sorted(
        (s for s in ranked if s.is_open_weights is not True),
        key=lambda s: getattr(s, key),
        reverse=reverse,
    )
    combined = open_ranked[:limit_each] + closed_ranked[:limit_each]
    combined.sort(key=lambda s: getattr(s, key), reverse=reverse)
    return [benchmark_score_to_dict(s) for s in combined]


@bp.get("/api/benchmarks/table")
def benchmark_table():
    """One comparison table that mirrors artificialanalysis.ai/models: every
    scored model with an Intelligence Index, sorted by Intelligence Index
    descending, top ``limit`` (default 25 — AA's own default page size), with all
    columns (intelligence, coding, agentic, price, speed, latency, context).

    Deliberately NO balanced open/closed split and NO famous-only cost filter —
    those re-orderings are what made our board diverge from AA's page. This is a
    straight top-N-by-intelligence view, exactly like AA's default sort.

    Query param: ?limit=N (default 25).
    """
    limit = request.args.get("limit", default=25, type=int)
    session = get_session()
    try:
        scores = session.query(BenchmarkScore).all()
        ranked = [s for s in scores if s.intelligence is not None]
        ranked.sort(key=lambda s: s.intelligence, reverse=True)
        generated_at = max((s.generated_at for s in scores), default=None)
        source_note = scores[0].source_note if scores else None
        return jsonify(
            {
                "enabled": Config.BENCHMARK_ENABLED,
                "generated_at": generated_at.isoformat() if generated_at else None,
                "source_note": source_note,
                "models": [benchmark_score_to_dict(s) for s in ranked[:limit]],
            }
        )
    finally:
        session.close()


@bp.get("/api/benchmarks")
def list_benchmarks():
    """Category leaderboards from one scored set. Intelligence/coding/math/agentic
    rank descending (higher is better), speed descends (faster), cost and price
    ascend (cheaper). Coding/math/agentic are only populated when the scoreboard is
    sourced from the Artificial Analysis API; they come back empty otherwise, and
    the frontend hides the tabs for empty categories. Cost and price are additionally
    restricted to a curated set of well-known labs (see _FAMOUS_COMPANIES) so
    the cheapest slots aren't dominated by obscure niche providers. Every score dict
    carries latency and context_length so each category tab can show those columns.

    Query params: ?limit=N (default 10, total rows per category) and
    ?balanced=1 (default off) to guarantee up to limit/2 open-weight and
    limit/2 closed models each, re-merged by rank — used by the full
    Benchmarks page's top-20 view; the Feed sidebar panel keeps the plain
    flat top-10 default.
    """
    limit = request.args.get("limit", default=10, type=int)
    balanced = request.args.get("balanced", default="").lower() in ("1", "true", "yes")
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
                "intelligence": _top(scores, "intelligence", reverse=True, limit=limit, balanced=balanced),
                "coding": _top(scores, "coding", reverse=True, limit=limit, balanced=balanced),
                "math": _top(scores, "math", reverse=True, limit=limit, balanced=balanced),
                "agentic": _top(scores, "agentic", reverse=True, limit=limit, balanced=balanced),
                "speed": _top(scores, "speed", reverse=True, limit=limit, balanced=balanced),
                "cost": _top(
                    scores, "cost", reverse=False, limit=limit, balanced=balanced, famous_only=True
                ),
                # Blended $/M price (AA's "Price" column), cheapest first. Like the
                # cost tab it's restricted to well-known labs (see _FAMOUS_COMPANIES)
                # so the cheapest slots aren't dominated by obscure niche providers.
                "price": _top(
                    scores, "price", reverse=False, limit=limit, balanced=balanced, famous_only=True
                ),
            }
        )
    finally:
        session.close()
