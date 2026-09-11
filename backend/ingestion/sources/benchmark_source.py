"""Populates the "Model Benchmarks" scoreboard (intelligence / speed / cost).

Primary source is the Artificial Analysis Data API — real, measured data for
each model's intelligence index, output speed, and API pricing. No LLM is
involved, so the numbers can't hallucinate or drift the way a model's
recollection can, and it costs nothing beyond a single HTTP request (free tier:
1,000 requests/day). This is the same source the LLM prompt below already cited
("Artificial Analysis Intelligence Index"), so we now read it directly.

When no Artificial Analysis key is configured, it falls back to the older
approach: asking a configurable LLM (BENCHMARK_MODEL, optionally web-grounded)
to produce the numbers.

Best-effort, like ai_summarize: any failure leaves the previous rows in place
(we only replace them once a fresh set parses cleanly), so a bad run never
blanks the panel.
"""

import json
import logging
import re
from datetime import datetime, timezone

import requests

from config import Config
from models import BenchmarkScore, ModelRelease

logger = logging.getLogger(__name__)

# Loose key for matching AA model names to catalog names ('GPT-5.1' ~ 'gpt 5 1').
_NORMALIZE_NAME = re.compile(r"[^a-z0-9]+")


def _match_key(name: str) -> str:
    return _NORMALIZE_NAME.sub(" ", (name or "").lower()).strip()


# --- Open-weights vs closed classification ------------------------------------
# The Artificial Analysis Data API only reports a model's license/open-weights
# status on its Pro tier ("licensing.is_open_weights"); this project uses the
# free tier, so that field is absent from every response we actually get. We
# classify by lab instead, since almost every lab in the AA dataset either
# ships open weights for everything it releases or nothing at all. A handful of
# labs straddle the line (Google, Mistral, Meta ship one or two closed/hosted
# models alongside their open releases) — those are handled by name overrides.
_OPEN_COMPANIES = {
    "meta", "meta ai", "mistral", "mistral ai", "deepseek", "alibaba", "qwen",
    "moonshot ai", "moonshot", "zhipu ai", "zhipu", "z.ai", "01.ai", "01 ai",
    "minimax", "nvidia", "databricks", "stability ai", "allen institute for ai",
    "ai2", "ibm", "snowflake", "tii", "technology innovation institute",
    "microsoft",  # Phi models are open-weight; Microsoft's closed models are OpenAI's
}
_CLOSED_COMPANIES = {
    "openai", "anthropic", "google", "google deepmind", "xai", "amazon",
    "cohere", "inflection", "reka", "reka ai", "perplexity", "ai21",
    "ai21 labs", "baidu", "bytedance",
}
# Name substrings that override the company-level default above (checked
# case-insensitively), for labs whose catalog mixes open and closed models.
_OPEN_NAME_OVERRIDES = ("gemma", "llama", "codestral", "mixtral", "phi-", "phi ")
_CLOSED_NAME_OVERRIDES = ("mistral large", "mistral medium", "le chat")


def _classify_open_weights(company: str | None, model_name: str) -> bool | None:
    name_lower = (model_name or "").lower()
    for needle in _CLOSED_NAME_OVERRIDES:
        if needle in name_lower:
            return False
    for needle in _OPEN_NAME_OVERRIDES:
        if needle in name_lower:
            return True

    company_key = (company or "").strip().lower()
    if company_key in _OPEN_COMPANIES:
        return True
    if company_key in _CLOSED_COMPANIES:
        return False
    return None

# Cost is normalized to one "standard task" so the cheapest/most-expensive
# ranking is comparable across models regardless of their per-token prices.
STANDARD_TASK_INPUT_TOKENS = 10_000
STANDARD_TASK_OUTPUT_TOKENS = 2_000

PROMPT = """You are compiling a current AI model benchmark scoreboard for a \
news dashboard. Using up-to-date public data, list the {n} most notable large \
language models available right now, chosen to span the full range from \
frontier flagships to fast/cheap small models (so the speed and cost rankings \
are meaningful, not just the smartest models).

For each model return these fields:
- "model": the exact current model name, including version (e.g. "Claude Opus 5", "Gemini 3.1 Pro").
- "company": the lab that makes it (e.g. "OpenAI", "Google", "Anthropic", "DeepSeek", "Alibaba", "xAI", "Meta", "Mistral", "Moonshot").
- "intelligence": composite intelligence score from 0-100 (higher is smarter), aligned to well-known aggregate benchmarks such as the Artificial Analysis Intelligence Index (rescaled to 0-100).
- "speed": typical output generation speed in tokens per second (higher is faster).
- "cost": estimated cost in US dollars to complete one standard task of ~10,000 input tokens and ~2,000 output tokens at current API list prices (lower is cheaper).

Include strong Chinese labs (DeepSeek, Alibaba/Qwen, Moonshot/Kimi, Zhipu/GLM, MiniMax) where they rank.

Respond with ONLY a strict JSON array of objects with exactly those five keys, \
no markdown fences, no commentary. Use realistic current numbers; do not \
invent models that do not exist."""


def _generate_raw() -> str | None:
    """Call the configured benchmark model (with grounding when enabled) and
    return its raw text response, or None if unavailable."""
    if not (Config.BENCHMARK_ENABLED and Config.BENCHMARK_API_KEY):
        return None

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=Config.BENCHMARK_API_KEY)
    # A larger request than the target count so each per-metric top-10 has a real
    # pool to rank (cheapest/fastest models differ from the smartest ones).
    n_requested = max(Config.BENCHMARK_TOP_N * 3, 25)
    prompt = PROMPT.format(n=n_requested)
    logger.info(
        "benchmark: calling model=%s grounding=%s requesting=%d models (prompt=%d chars)",
        Config.BENCHMARK_MODEL,
        "on" if Config.BENCHMARK_USE_GROUNDING else "off",
        n_requested,
        len(prompt),
    )

    # Gemini 2.0+/3.x web grounding is the GoogleSearch tool (the older
    # google_search_retrieval / dynamic-retrieval tool is rejected by these
    # models). Try grounded first, then fall back to an ungrounded call so a
    # failure degrades to "stale but working" instead of failing outright.
    timeout_ms = int(Config.BENCHMARK_REQUEST_TIMEOUT * 1000)
    tool_variants = []
    if Config.BENCHMARK_USE_GROUNDING:
        tool_variants.append(
            ("google_search", [types.Tool(google_search=types.GoogleSearch())])
        )
    tool_variants.append(("ungrounded", None))  # fallback, always last

    last_exc = None
    for label, tools in tool_variants:
        try:
            logger.info("benchmark: attempt via %s …", label)
            config = types.GenerateContentConfig(
                tools=tools,
                http_options=types.HttpOptions(timeout=timeout_ms),
            )
            response = client.models.generate_content(
                model=Config.BENCHMARK_MODEL,
                contents=prompt,
                config=config,
            )
            _log_usage(label, response)
            if tools is None and Config.BENCHMARK_USE_GROUNDING:
                logger.warning(
                    "benchmark: grounding unavailable for %s — using ungrounded "
                    "output (numbers may be stale)",
                    Config.BENCHMARK_MODEL,
                )
            text = response.text
            logger.info(
                "benchmark: %s returned %d chars of text", label, len(text or "")
            )
            return text
        except Exception as exc:  # try the next variant
            last_exc = exc
            logger.warning("benchmark: attempt via %s failed: %s", label, exc)
            continue

    logger.error("benchmark generation failed — all attempts exhausted", exc_info=last_exc)
    return None


def _log_usage(label: str, response) -> None:
    """Log token usage from a Gemini response. Best-effort: the usage field's
    shape varies across SDK versions, so never let it raise."""
    try:
        um = getattr(response, "usage_metadata", None)
        if um is None:
            logger.info("benchmark: %s — no token usage reported", label)
            return
        prompt_tok = getattr(um, "prompt_token_count", None)
        out_tok = getattr(um, "candidates_token_count", None)
        total_tok = getattr(um, "total_token_count", None)
        logger.info(
            "benchmark: %s token usage — prompt=%s output=%s total=%s",
            label,
            prompt_tok,
            out_tok,
            total_tok,
        )
    except Exception:  # logging must never break generation
        logger.debug("benchmark: could not read token usage", exc_info=True)


def _parse(text: str) -> list[dict]:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text[text.find("["):]
    # Trim anything after the closing bracket (stray grounding citations, etc.).
    end = text.rfind("]")
    if end != -1:
        text = text[: end + 1]
    data = json.loads(text)
    rows = []
    for item in data:
        try:
            name = str(item["model"]).strip()
            if not name:
                continue
            company = str(item.get("company", "")).strip() or None
            rows.append(
                {
                    "model_name": name,
                    "company": company,
                    "intelligence": _num(item.get("intelligence")),
                    "speed": _num(item.get("speed")),
                    "cost": _num(item.get("cost")),
                    "is_open_weights": _classify_open_weights(company, name),
                }
            )
        except Exception:
            continue
    return rows


def _num(value):
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


# --- Artificial Analysis Data API (primary source) ---------------------------


def _dig(obj, *paths):
    """Return the first non-None value found at any of the given dotted key
    paths, tolerating the API nesting its fields slightly differently across
    versions (e.g. "evaluations.artificial_analysis_intelligence_index")."""
    for path in paths:
        cur = obj
        for key in path.split("."):
            if not isinstance(cur, dict):
                cur = None
                break
            cur = cur.get(key)
        if cur is not None:
            return cur
    return None


def _standard_task_cost(item) -> float | None:
    """USD to run one standard task (~10k input + ~2k output tokens) at the
    model's list price. Prices in the API are per 1M tokens."""
    in_price = _num(
        _dig(item, "pricing.price_1m_input_tokens", "price.price_1m_input_tokens")
    )
    out_price = _num(
        _dig(item, "pricing.price_1m_output_tokens", "price.price_1m_output_tokens")
    )
    if in_price is None and out_price is None:
        # Fall back to a blended per-1M price if the split isn't available.
        blended = _num(
            _dig(item, "pricing.price_1m_blended_3_to_1", "price.price_1m_blended_3_to_1")
        )
        if blended is None:
            return None
        total_tokens = STANDARD_TASK_INPUT_TOKENS + STANDARD_TASK_OUTPUT_TOKENS
        return round(blended * total_tokens / 1_000_000, 4)
    return round(
        (in_price or 0.0) * STANDARD_TASK_INPUT_TOKENS / 1_000_000
        + (out_price or 0.0) * STANDARD_TASK_OUTPUT_TOKENS / 1_000_000,
        4,
    )


def _parse_artificial_analysis(payload) -> list[dict]:
    data = payload.get("data") if isinstance(payload, dict) else payload
    if not isinstance(data, list):
        return []
    rows = []
    for item in data:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or item.get("slug") or "").strip()
        if not name:
            continue
        company = _dig(item, "model_creator.name", "model_creator.slug")
        intelligence = _num(
            _dig(
                item,
                "evaluations.artificial_analysis_intelligence_index",
                "artificial_analysis_intelligence_index",
            )
        )
        speed = _num(
            _dig(
                item,
                "median_output_tokens_per_second",
                "evaluations.median_output_tokens_per_second",
                "performance.median_output_tokens_per_second",
            )
        )
        cost = _standard_task_cost(item)
        # Per-category indices power the Coding / Math / Agentic leaderboards.
        # Only the AA source has these; the LLM fallback leaves them NULL.
        coding = _num(
            _dig(
                item,
                "evaluations.artificial_analysis_coding_index",
                "artificial_analysis_coding_index",
            )
        )
        math = _num(
            _dig(
                item,
                "evaluations.artificial_analysis_math_index",
                "artificial_analysis_math_index",
            )
        )
        agentic = _num(
            _dig(
                item,
                "evaluations.artificial_analysis_agentic_index",
                "artificial_analysis_agentic_index",
            )
        )
        company = str(company).strip() if company else None
        # Real license data (Pro tier only) wins when present; otherwise fall
        # back to the company/name heuristic below.
        is_open_weights = _dig(item, "licensing.is_open_weights", "is_open_weights")
        if not isinstance(is_open_weights, bool):
            is_open_weights = _classify_open_weights(company, name)
        # Skip rows with nothing to rank on — an entry with no metric at all is
        # noise in every leaderboard.
        if intelligence is None and speed is None and cost is None:
            continue
        rows.append(
            {
                "model_name": name,
                "company": company,
                "intelligence": intelligence,
                "speed": speed,
                "cost": cost,
                "coding": coding,
                "math": math,
                "agentic": agentic,
                "is_open_weights": is_open_weights,
            }
        )
    return rows


def _fetch_from_artificial_analysis() -> list[dict] | None:
    """Pull the model catalog from the Artificial Analysis Data API and map it
    to benchmark rows. Returns None if no key is configured or the request fails
    (so the caller can fall back to the LLM generator)."""
    if not Config.ARTIFICIAL_ANALYSIS_API_KEY:
        return None

    logger.info(
        "benchmark: fetching from Artificial Analysis Data API (%s)",
        Config.ARTIFICIAL_ANALYSIS_API_URL,
    )
    try:
        resp = requests.get(
            Config.ARTIFICIAL_ANALYSIS_API_URL,
            headers={"x-api-key": Config.ARTIFICIAL_ANALYSIS_API_KEY},
            timeout=Config.BENCHMARK_REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        payload = resp.json()
    except Exception as exc:
        logger.warning("benchmark: Artificial Analysis request failed: %s", exc)
        return None

    try:
        rows = _parse_artificial_analysis(payload)
    except Exception:
        logger.exception("benchmark: could not parse Artificial Analysis response")
        return None

    logger.info("benchmark: Artificial Analysis returned %d usable models", len(rows))
    return rows


def _update_catalog_scores(session, rows: list[dict]) -> int:
    """Match AA intelligence scores onto existing Models-catalog rows by name so
    the Models page can show a per-model quality score. Best-effort; returns the
    number of model_releases rows updated. Only meaningful for AA-sourced rows —
    the LLM fallback's guessed numbers are not written onto the catalog."""
    scored = {
        _match_key(r["model_name"]): r["intelligence"]
        for r in rows
        if r.get("intelligence") is not None
    }
    if not scored:
        return 0
    updated = 0
    for release in session.query(ModelRelease).all():
        score = scored.get(_match_key(release.model_name))
        if score is not None and release.intelligence_index != score:
            release.intelligence_index = score
            updated += 1
    if updated:
        session.commit()
    logger.info("benchmark: set intelligence_index on %d catalog rows", updated)
    return updated


def _generate_from_llm() -> list[dict] | None:
    """Fallback: ask the configured LLM to produce the scoreboard. Returns None
    if generation returned nothing or couldn't be parsed."""
    raw = _generate_raw()
    if not raw:
        logger.warning("benchmark: LLM generation returned no text")
        return None
    try:
        rows = _parse(raw)
    except Exception:
        logger.exception(
            "benchmark: could not parse LLM output; first 500 chars: %r", raw[:500]
        )
        return None
    if not rows:
        logger.warning(
            "benchmark: LLM returned no usable rows; first 500 chars: %r", raw[:500]
        )
    return rows or None


def fetch_and_store(session) -> int:
    """Refresh the scoreboard and atomically replace the table. Prefers the
    Artificial Analysis Data API; falls back to the LLM generator when no AA key
    is set or the API is unavailable. Returns the number of rows written (0 when
    disabled or on any failure — existing rows are left untouched unless a fresh
    set parses cleanly)."""
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    rows = _fetch_from_artificial_analysis()
    from_aa = bool(rows)
    if rows:
        note = f"Artificial Analysis Data API, {date}"
    else:
        if Config.ARTIFICIAL_ANALYSIS_API_KEY:
            logger.warning(
                "benchmark: Artificial Analysis unavailable — falling back to LLM"
            )
        rows = _generate_from_llm()
        note = "{model}{grounded}, {date}".format(
            model=Config.BENCHMARK_MODEL,
            grounded=" · web-grounded" if Config.BENCHMARK_USE_GROUNDING else "",
            date=date,
        )

    if not rows:
        logger.warning("benchmark: no rows produced — keeping existing rows")
        return 0

    logger.info("benchmark: writing %d models (source: %s)", len(rows), note)
    preview = ", ".join(f"{r['model_name']} (I={r['intelligence']})" for r in rows[:3])
    logger.info("benchmark: sample — %s", preview)

    session.query(BenchmarkScore).delete()
    for r in rows:
        session.add(BenchmarkScore(source_note=note, **r))
    session.commit()

    # Enrich the Models catalog with per-model intelligence scores, but only from
    # the real AA data — never from the LLM fallback's guesses. Isolated so a
    # matching failure can't roll back the committed scoreboard.
    if from_aa:
        try:
            _update_catalog_scores(session, rows)
        except Exception:
            session.rollback()
            logger.exception("benchmark: catalog intelligence_index update failed")

    return len(rows)
