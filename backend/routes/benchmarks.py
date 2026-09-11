import re

from flask import Blueprint, jsonify, request

from config import Config
from models import BenchmarkScore, ModelRelease
from services.db import get_session
from services.serialize import benchmark_score_to_dict

bp = Blueprint("benchmarks", __name__)


def _norm_name(name: str) -> str:
    """Loose model-name key for matching benchmark rows to catalog rows. Strips
    parenthetical qualifiers ('(high)', '(Non-reasoning)') and non-alphanumerics
    so 'GPT-5.1 (high)' and 'gpt 5 1' collapse to the same key."""
    n = (name or "").lower()
    n = re.sub(r"\([^)]*\)", " ", n)
    return re.sub(r"[^a-z0-9]+", " ", n).strip()


def _context_lookup(session) -> dict:
    """Map normalized model name -> context window from the Models catalog
    (populated from OpenRouter). The Artificial Analysis *free* endpoint doesn't
    return a context window, so we borrow it from the catalog at read time,
    filling the Context column without needing a benchmark re-ingest."""
    out: dict = {}
    for r in session.query(ModelRelease).all():
        if r.context_length:
            out.setdefault(_norm_name(r.model_name), r.context_length)
    return out

# Cost ranks every scored model ascending by price, so left unfiltered the
# cheapest slots go to obscure/niche providers rather than the well-known labs
# people actually compare prices across. Restrict the cost category to this
# curated set of ~20 major labs before ranking. Keys are lower-cased company
# names; several labs appear under more than one label from the AA data (e.g.
# "google" / "google deepmind"), so include each variant we've seen.
_FAMOUS_COMPANIES = {
    "openai", "anthropic", "google", "google deepmind", "meta", "meta ai",
    "xai", "deepseek", "alibaba", "qwen", "mistral", "mistral ai",
    "microsoft", "amazon", "amazon web services", "aws", "moonshot ai", "moonshot",
    "cohere", "ai21", "ai21 labs", "reka", "reka ai", "nvidia", "perplexity",
    "zhipu", "zhipu ai", "z.ai", "baidu", "tencent", "minimax", "ibm",
    "01.ai", "01 ai", "yi", "databricks", "lg", "lg ai research", "servicenow",
    "nous research", "nous",
}


def _is_famous(score) -> bool:
    return (score.company or "").strip().lower() in _FAMOUS_COMPANIES


def _top_per_company(scores, key):
    """Collapse to one representative model per company: each company's *top*
    model — the highest-intelligence one it has (falling back to the best value
    of ``key`` when intelligence is missing). This is what makes the cost board
    read as "top famous companies, each shown via its current flagship / most-
    used top model" rather than the same lab appearing many times with cheap
    legacy variants.

    The reps are ordered by intelligence (prominence) descending, NOT by cost —
    the user wants the heavily-used top models shown with their cost, not the
    cheapest models ranked first. ``key`` (cost) is only used as the fallback
    representative-selector and as an ordering tie-break."""
    best_by_company: dict = {}
    for s in scores:
        company = (s.company or "").strip().lower()
        rank_val = s.intelligence if s.intelligence is not None else getattr(s, key)
        cur = best_by_company.get(company)
        if cur is None or rank_val > cur[0]:
            best_by_company[company] = (rank_val, s)
    reps = [pair[1] for pair in best_by_company.values()]
    reps.sort(
        key=lambda s: (
            s.intelligence if s.intelligence is not None else float("-inf"),
            -(getattr(s, key) or 0),
        ),
        reverse=True,
    )
    return reps


def _dump(score, ctx_lookup=None) -> dict:
    """Serialize one score, backfilling context_length from the catalog lookup
    when the benchmark row itself has none (AA's free tier omits it)."""
    d = benchmark_score_to_dict(score)
    if ctx_lookup is not None and d.get("context_length") is None:
        d["context_length"] = ctx_lookup.get(_norm_name(score.model_name))
    return d


def _top(scores, key, reverse, limit=10, balanced=False, famous_only=False,
         ctx_lookup=None, positive=False, per_company=False):
    ranked = [s for s in scores if getattr(s, key) is not None]
    # For money metrics a stored 0.0 means "no active paid provider / no pricing
    # data" (see benchmark_source._standard_task_cost), not "free" — drop them so
    # they don't fraudulently occupy the cheapest slots when ranking ascending.
    if positive:
        ranked = [s for s in ranked if getattr(s, key) > 0]
    if famous_only:
        ranked = [s for s in ranked if _is_famous(s)]
    # Cost: one representative (top) model per company, ordered by prominence
    # (intelligence), not cheapest-first. Keeps the board to ~20 famous companies'
    # heavily-used flagship models rather than repeating a lab's cheap variants.
    if per_company:
        reps = _top_per_company(ranked, key)
        return [_dump(s, ctx_lookup) for s in reps[:limit]]
    if not balanced:
        ranked.sort(key=lambda s: getattr(s, key), reverse=reverse)
        return [_dump(s, ctx_lookup) for s in ranked[:limit]]

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
    return [_dump(s, ctx_lookup) for s in combined]


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
    restricted to a curated set of well-known labs (see _FAMOUS_COMPANIES) and
    collapsed to one representative (top) model per company (see _top_per_company),
    so the board shows the top ~20 famous companies via their current flagship model
    rather than a lab's cheap legacy variants. Every score dict
    carries latency and context_length so each category tab can show those columns;
    context_length is backfilled from the Models catalog (_context_lookup) because
    the AA free endpoint doesn't return a context window.

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
        ctx_lookup = _context_lookup(session)
        generated_at = max((s.generated_at for s in scores), default=None)
        source_note = scores[0].source_note if scores else None

        def top(key, reverse, famous_only=False, positive=False, per_company=False):
            return _top(
                scores, key, reverse=reverse, limit=limit, balanced=balanced,
                famous_only=famous_only, ctx_lookup=ctx_lookup,
                positive=positive, per_company=per_company,
            )

        return jsonify(
            {
                "enabled": Config.BENCHMARK_ENABLED,
                "generated_at": generated_at.isoformat() if generated_at else None,
                "source_note": source_note,
                "intelligence": top("intelligence", reverse=True),
                "coding": top("coding", reverse=True),
                "math": top("math", reverse=True),
                "agentic": top("agentic", reverse=True),
                "speed": top("speed", reverse=True),
                # AA's real per-task cost (accounts for reasoning models' token use),
                # restricted to well-known labs (_FAMOUS_COMPANIES) and collapsed to
                # one representative (top) model per company, ordered by prominence
                # (intelligence) — NOT cheapest-first — so the board reads as "top
                # famous companies' heavily-used flagship models, with cost". The
                # caller's limit applies (the Benchmarks page requests 25, which the
                # one-per-company collapse naturally caps at ~20 famous labs).
                "cost": top("cost", reverse=False, famous_only=True, positive=True,
                            per_company=True),
                # Blended $/M price (AA's "Price" column). Absent on the AA free
                # tier, so this is typically empty; kept for API back-compat.
                "price": top("price", reverse=False, famous_only=True, positive=True),
            }
        )
    finally:
        session.close()
