"""Bounded LLM summarization/tagging for newly ingested articles.

Best-effort: any failure (missing key, quota, network) falls back to leaving
ai_summary unset — the raw source summary is used everywhere the UI needs
one, so ingestion never blocks on this.
"""

import json
import logging

from config import Config

logger = logging.getLogger(__name__)

_model = None


def _get_model():
    global _model
    if _model is not None:
        return _model
    if not (Config.AI_SUMMARIZE_ENABLED and Config.GEMINI_API_KEY):
        return None
    import google.generativeai as genai

    genai.configure(api_key=Config.GEMINI_API_KEY)
    _model = genai.GenerativeModel(Config.GEMINI_MODEL)
    return _model


PROMPT = """You summarize AI-industry news for a dashboard. Given the title and \
raw summary of one article, return strict JSON with keys:
- "summary": a neutral 2-3 sentence summary (no marketing language)
- "companies": list of company names clearly involved (e.g. ["OpenAI", "Microsoft"])
- "models": list of specific AI model names mentioned (e.g. ["GPT-5", "Llama 4"]) or []
- "topics": list of short topic tags (e.g. ["funding", "benchmark", "release"])

Title: {title}
Raw summary: {raw_summary}

Respond with ONLY the JSON object, no markdown fences."""


def summarize_and_tag(title: str, raw_summary: str) -> dict | None:
    model = _get_model()
    if model is None:
        return None
    try:
        response = model.generate_content(
            PROMPT.format(title=title, raw_summary=raw_summary or "")
        )
        text = response.text.strip()
        if text.startswith("```"):
            text = text.strip("`")
            text = text[text.find("{"):]
        return json.loads(text)
    except Exception:
        logger.exception("AI summarize/tag failed for article %r", title)
        return None
