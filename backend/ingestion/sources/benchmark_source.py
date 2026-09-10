"""Generates the "Model Benchmarks" scoreboard (intelligence / speed / cost)
using a configurable LLM — see BENCHMARK_MODEL in config.py.

This deliberately uses a SEPARATE model from the per-article summarizer so it
can be a stronger, web-grounded model. Accuracy hinges on grounding: with
BENCHMARK_USE_GROUNDING the model answers from live Google Search results
(current standings); without it, the numbers are the model's stale guess.

Best-effort, like ai_summarize: any failure leaves the previous rows in place
(we only replace them once a fresh generation parses cleanly), so a bad run
never blanks the panel.
"""

import json
import logging
from datetime import datetime, timezone

from config import Config
from models import BenchmarkScore

logger = logging.getLogger(__name__)

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

    import google.generativeai as genai

    genai.configure(api_key=Config.BENCHMARK_API_KEY)
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

    # Grounding tool names differ across google-generativeai versions; try the
    # known spellings, then fall back to an ungrounded call so a version mismatch
    # degrades to "stale but working" instead of failing outright.
    tool_variants = []
    if Config.BENCHMARK_USE_GROUNDING:
        tool_variants = ["google_search", "google_search_retrieval"]
    tool_variants.append(None)  # ungrounded fallback, always last

    last_exc = None
    for tool in tool_variants:
        label = tool if tool else "ungrounded"
        try:
            logger.info("benchmark: attempt via %s …", label)
            model = (
                genai.GenerativeModel(Config.BENCHMARK_MODEL, tools=tool)
                if tool
                else genai.GenerativeModel(Config.BENCHMARK_MODEL)
            )
            response = model.generate_content(prompt)
            _log_usage(label, response)
            if tool is None and Config.BENCHMARK_USE_GROUNDING:
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
    shape varies across google-generativeai versions, so never let it raise."""
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
            rows.append(
                {
                    "model_name": name,
                    "company": (str(item.get("company", "")).strip() or None),
                    "intelligence": _num(item.get("intelligence")),
                    "speed": _num(item.get("speed")),
                    "cost": _num(item.get("cost")),
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


def fetch_and_store(session) -> int:
    """Generate a fresh scoreboard and atomically replace the table. Returns the
    number of rows written (0 when disabled or on any failure — existing rows are
    left untouched unless a fresh set parses cleanly)."""
    raw = _generate_raw()
    if not raw:
        logger.warning("benchmark: generation returned no text — keeping existing rows")
        return 0

    try:
        rows = _parse(raw)
    except Exception:
        # Log a snippet of what we got so a bad/non-JSON response is diagnosable.
        logger.exception(
            "benchmark: could not parse model output; first 500 chars: %r",
            raw[:500],
        )
        return 0

    if not rows:
        logger.warning(
            "benchmark: model returned no usable rows; first 500 chars: %r", raw[:500]
        )
        return 0

    logger.info("benchmark: parsed %d models from response", len(rows))
    preview = ", ".join(
        f"{r['model_name']} (I={r['intelligence']})" for r in rows[:3]
    )
    logger.info("benchmark: sample — %s", preview)

    note = "{model}{grounded}, {date}".format(
        model=Config.BENCHMARK_MODEL,
        grounded=" · web-grounded" if Config.BENCHMARK_USE_GROUNDING else "",
        date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    )

    session.query(BenchmarkScore).delete()
    for r in rows:
        session.add(BenchmarkScore(source_note=note, **r))
    session.commit()
    return len(rows)
