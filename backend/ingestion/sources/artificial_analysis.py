"""Artificial Analysis API source — real, independently-measured model data.

Two things this feeds, both best-effort (a failure leaves existing rows intact,
exactly like benchmark_source and openrouter_models):

1. The "Model Benchmarks" scoreboard (benchmark_scores table). This is the
   PREFERRED source when AA_API_KEY is set — it replaces the grounded-LLM guess
   in benchmark_source.py with authoritative numbers, and additionally fills the
   per-category (coding / math / agentic) indices the LLM source can't produce.

2. Per-model intelligence scores on the Models catalog page (model_releases
   .intelligence_index), matched onto the OpenRouter-sourced catalog by name.

The API: GET {AA_BASE_URL}/data/llms/models with an `x-api-key` header. Response
is a JSON envelope whose model list lives under `data` (a few deployments nest
it as `data.data`); each model carries an `evaluations` object of index scores,
a `pricing` object (USD per 1M tokens), a median output speed, and creator
metadata. Field names have shifted across API versions, so every field is read
through tolerant helpers that try several spellings and never raise.

Docs: https://artificialanalysis.ai/data-api/docs
"""

import logging
import re
from datetime import datetime, timezone

import requests

from config import Config
from models import BenchmarkScore, ModelRelease

logger = logging.getLogger(__name__)

# Task shape used to turn per-token pricing into a single "cost per task" number,
# kept identical to benchmark_source so the panel's Cost tab stays comparable
# whichever source produced the row.
TASK_INPUT_TOKENS = 10_000
TASK_OUTPUT_TOKENS = 2_000


# --- tolerant field access ----------------------------------------------------

def _num(value):
    """Coerce to float, or None. Tolerates strings, None, and junk."""
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _first(d: dict, *keys):
    """First present, non-None value among `keys` in dict `d`."""
    if not isinstance(d, dict):
        return None
    for k in keys:
        if k in d and d[k] is not None:
            return d[k]
    return None


def _first_num(d: dict, *keys):
    return _num(_first(d, *keys))


def _creator_name(record: dict) -> str | None:
    """The lab that makes the model. AA nests this as an object under a few
    different keys; fall back to any flat string field."""
    for key in ("model_creator", "creator", "organization", "provider"):
        val = record.get(key)
        if isinstance(val, dict):
            name = _first(val, "name", "slug", "id")
            if name:
                return str(name).strip()
        elif isinstance(val, str) and val.strip():
            return val.strip()
    return None


def _release_date(record: dict) -> datetime | None:
    raw = _first(record, "release_date", "released_at", "announced_date", "date")
    if not raw:
        return None
    text = str(raw).strip().replace("Z", "+00:00")
    for parse in (
        datetime.fromisoformat,
        lambda s: datetime.strptime(s, "%Y-%m-%d"),
    ):
        try:
            dt = parse(text)
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            continue
    return None


def _cost_per_task(pricing: dict) -> float | None:
    """USD to run one standard task (~10k in + 2k out). Prefer explicit
    input/output pricing; fall back to a blended price if that's all AA returns
    (free tier omits blended)."""
    inp = _first_num(
        pricing, "price_1m_input_tokens", "price_input_tokens", "input", "prompt"
    )
    out = _first_num(
        pricing, "price_1m_output_tokens", "price_output_tokens", "output", "completion"
    )
    if inp is not None and out is not None:
        return round(
            inp * TASK_INPUT_TOKENS / 1e6 + out * TASK_OUTPUT_TOKENS / 1e6, 6
        )
    blended = _first_num(
        pricing, "price_1m_blended_3_to_1", "price_1m_blended", "blended"
    )
    if blended is not None:
        return round(blended * (TASK_INPUT_TOKENS + TASK_OUTPUT_TOKENS) / 1e6, 6)
    return None


def _index(evals: dict, *keys):
    return _first_num(evals, *keys)


def normalize(record: dict) -> dict | None:
    """Raw AA model record -> flat row. Returns None if there's no usable name."""
    if not isinstance(record, dict):
        return None
    name = _first(record, "name", "model_name", "slug")
    if not name:
        return None
    name = str(name).strip()
    if not name:
        return None

    evals = record.get("evaluations") or record.get("benchmarks") or {}
    if not isinstance(evals, dict):
        evals = {}
    pricing = record.get("pricing") or record.get("price") or {}
    if not isinstance(pricing, dict):
        pricing = {}

    return {
        "model_name": name,
        "company": _creator_name(record),
        "intelligence": _index(
            evals,
            "artificial_analysis_intelligence_index",
            "intelligence_index",
            "intelligence",
        ),
        "coding": _index(
            evals, "artificial_analysis_coding_index", "coding_index", "coding"
        ),
        "math": _index(
            evals, "artificial_analysis_math_index", "math_index", "math"
        ),
        "agentic": _index(
            evals, "artificial_analysis_agentic_index", "agentic_index", "agentic"
        ),
        "speed": _first_num(
            record,
            "median_output_tokens_per_second",
            "output_tokens_per_second",
            "median_output_speed",
        ),
        "cost": _cost_per_task(pricing),
        "release_date": _release_date(record),
    }


# --- fetch --------------------------------------------------------------------

def fetch_models() -> list[dict]:
    """Return normalized model rows from the AA API, or [] if disabled/unavailable."""
    if not (Config.AA_ENABLED and Config.AA_API_KEY):
        return []

    url = f"{Config.AA_BASE_URL.rstrip('/')}/data/llms/models"
    logger.info("artificial_analysis: GET %s", url)
    resp = requests.get(
        url,
        headers={"x-api-key": Config.AA_API_KEY, "User-Agent": "AI-News/1.0"},
        timeout=Config.AA_REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    payload = resp.json()

    # Envelope: the model list is under `data`; some deployments double-wrap it.
    data = payload.get("data") if isinstance(payload, dict) else payload
    if isinstance(data, dict):
        data = data.get("data") or data.get("models") or []
    if not isinstance(data, list):
        logger.warning("artificial_analysis: unexpected payload shape — no model list")
        return []

    rows = [r for r in (normalize(m) for m in data) if r]
    logger.info("artificial_analysis: normalized %d models", len(rows))
    return rows


# --- name matching for the Models page ----------------------------------------

_NORMALIZE_NAME = re.compile(r"[^a-z0-9]+")


def _match_key(name: str) -> str:
    """Loose key for matching AA names to catalog names ('GPT-5.1' ~ 'gpt 5 1')."""
    return _NORMALIZE_NAME.sub(" ", (name or "").lower()).strip()


# --- store --------------------------------------------------------------------

def store_benchmarks(session, rows: list[dict]) -> int:
    """Atomically replace the benchmark_scores table with AA rows. Returns the
    number written (0 leaves the existing scoreboard untouched)."""
    usable = [r for r in rows if r["intelligence"] is not None or r["speed"] is not None]
    if not usable:
        logger.warning("artificial_analysis: no usable benchmark rows — keeping existing")
        return 0

    note = "Artificial Analysis, {}".format(
        datetime.now(timezone.utc).strftime("%Y-%m-%d")
    )
    session.query(BenchmarkScore).delete()
    for r in usable:
        session.add(
            BenchmarkScore(
                model_name=r["model_name"],
                company=r["company"],
                intelligence=r["intelligence"],
                speed=r["speed"],
                cost=r["cost"],
                coding=r["coding"],
                math=r["math"],
                agentic=r["agentic"],
                source_note=note,
            )
        )
    session.commit()
    logger.info("artificial_analysis: wrote %d benchmark rows", len(usable))
    return len(usable)


def update_model_scores(session, rows: list[dict]) -> int:
    """Match AA intelligence scores onto existing catalog rows by model name.
    Returns the number of model_releases rows updated."""
    scored = {
        _match_key(r["model_name"]): r["intelligence"]
        for r in rows
        if r["intelligence"] is not None
    }
    if not scored:
        return 0

    updated = 0
    for release in session.query(ModelRelease).all():
        score = scored.get(_match_key(release.model_name))
        if score is not None and release.intelligence_index != score:
            release.intelligence_index = score
            updated += 1
    session.commit()
    logger.info("artificial_analysis: updated intelligence_index on %d catalog rows", updated)
    return updated


def fetch_and_store(session) -> int:
    """Refresh the scoreboard AND enrich the catalog from one API fetch. Returns
    the number of benchmark rows written."""
    rows = fetch_models()
    if not rows:
        return 0
    written = store_benchmarks(session, rows)
    # Catalog enrichment is independent — do it even if the scoreboard write was
    # a no-op, and never let it undo a committed scoreboard.
    try:
        update_model_scores(session, rows)
    except Exception:
        session.rollback()
        logger.exception("artificial_analysis: catalog score update failed")
    return written
