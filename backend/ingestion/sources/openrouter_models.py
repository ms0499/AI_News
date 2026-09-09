"""Live model catalog from the OpenRouter models API — free, no API key.

One request to `/api/v1/models` returns the full cross-provider catalog (400+
models) with, per model: the exact versioned name, release date, context
window, input/output pricing, modalities, an editorial description, and the
knowledge cutoff. This is the durable, always-accurate answer to "what's each
company's latest model version" — it never goes stale the way a hand-curated
list does, because a scheduled refresh re-pulls it.

We keep only models from the real AI labs we track (PROVIDER_TO_COMPANY),
skip OpenRouter's variant aliases (ids containing ':' such as :batch/:free,
and the '~'-prefixed routing aliases), and require a text output so we list
LLMs rather than embedding/audio endpoints. Rows are upserted by catalog_key
(the OpenRouter id) so a refresh updates in place. The most recently created
model per company is flagged as that company's current/latest.
"""

import re
from datetime import datetime, timezone

import requests

MODELS_URL = "https://openrouter.ai/api/v1/models"

# OpenRouter descriptions embed markdown links like "[GPT-6 Astra](https://...)";
# render them as just their label text since the UI shows plain text.
_MD_LINK = re.compile(r"\[([^\]]+)\]\((?:[^)]+)\)")


def _clean_description(text: str | None) -> str | None:
    if not text:
        return None
    cleaned = _MD_LINK.sub(r"\1", text).strip()
    return cleaned[:2000] or None

# OpenRouter provider prefix -> the display name we track the company under.
# The name is slugified the same way get_or_create_company does, so these line
# up with the slugs used elsewhere (openai, anthropic, google-deepmind, ...).
PROVIDER_TO_COMPANY = {
    "openai": "OpenAI",
    "anthropic": "Anthropic",
    "google": "Google DeepMind",
    "x-ai": "xAI",
    "meta-llama": "Meta",
    "meta": "Meta",
    "mistralai": "Mistral",
    "deepseek": "DeepSeek",
    "qwen": "Alibaba",
    "moonshotai": "Moonshot AI",
    "nvidia": "Nvidia",
    "cohere": "Cohere",
    "amazon": "Amazon",
    "microsoft": "Microsoft",
    "perplexity": "Perplexity",
    "z-ai": "Zhipu AI",
    "minimax": "MiniMax",
    "baidu": "Baidu",
    "tencent": "Tencent",
    "bytedance": "ByteDance",
    "bytedance-seed": "ByteDance",
}


def _price_per_million(raw: str | None) -> float | None:
    """OpenRouter prices are USD per token as strings; show them per 1M tokens."""
    try:
        return round(float(raw) * 1_000_000, 4) if raw not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _released_at(created: int | None) -> datetime | None:
    if not created:
        return None
    return datetime.fromtimestamp(created, tz=timezone.utc)


def transform(raw_models: list[dict]) -> list[dict]:
    """Pure transform (no network/DB) so it's unit-testable: raw API records ->
    normalized catalog rows for the labs we track."""
    out = []
    for m in raw_models:
        model_id = m.get("id") or ""
        provider = model_id.split("/", 1)[0]
        company = PROVIDER_TO_COMPANY.get(provider)
        if not company:
            continue
        if ":" in model_id or provider.startswith("~"):
            continue  # variant aliases (:batch/:free) and routing aliases

        arch = m.get("architecture") or {}
        outputs = arch.get("output_modalities") or []
        if "text" not in outputs:
            continue  # keep LLMs, drop pure image/audio/embedding endpoints

        # Names come as "Vendor: Model Name" (e.g. "Google: Gemini 3.8 Flash");
        # drop the vendor prefix since rows are already grouped by company.
        name = m.get("name") or model_id
        if ": " in name:
            name = name.split(": ", 1)[1]

        pricing = m.get("pricing") or {}
        out.append(
            {
                "catalog_key": model_id,
                "company": company,
                "model_name": name,
                "release_date": _released_at(m.get("created")),
                "description": _clean_description(m.get("description")),
                "context_length": m.get("context_length"),
                "input_price": _price_per_million(pricing.get("prompt")),
                "output_price": _price_per_million(pricing.get("completion")),
                "modalities": arch.get("input_modalities") or [],
                "knowledge_cutoff": m.get("knowledge_cutoff"),
                "reference_url": f"https://openrouter.ai/{model_id}",
            }
        )
    return out


def fetch_catalog() -> list[dict]:
    resp = requests.get(MODELS_URL, timeout=30, headers={"User-Agent": "AI-News/1.0"})
    resp.raise_for_status()
    return transform(resp.json().get("data", []))


def fetch_and_store(session) -> int:
    """Upsert the catalog into model_releases (keyed by catalog_key) and mark the
    newest model per company as its current/latest. Returns rows upserted."""
    from models import ModelRelease
    from services.companies import get_or_create_company

    rows = fetch_catalog()
    if not rows:
        return 0

    touched_company_ids = set()
    for row in rows:
        company = get_or_create_company(session, row["company"])
        touched_company_ids.add(company.id)
        release = (
            session.query(ModelRelease)
            .filter_by(catalog_key=row["catalog_key"])
            .one_or_none()
        )
        if release is None:
            release = ModelRelease(catalog_key=row["catalog_key"])
            session.add(release)
        release.company_id = company.id
        release.model_name = row["model_name"]
        release.release_date = row["release_date"]
        # Don't clobber a good editorial description with an empty one.
        if row["description"]:
            release.description = row["description"]
        release.context_length = row["context_length"]
        release.input_price = row["input_price"]
        release.output_price = row["output_price"]
        release.modalities = row["modalities"]
        release.knowledge_cutoff = row["knowledge_cutoff"]
        release.reference_url = row["reference_url"]
    session.flush()

    # Recompute "latest" per company across catalog rows only (leave any older
    # article-derived rows' flags alone).
    for company_id in touched_company_ids:
        catalog_rows = (
            session.query(ModelRelease)
            .filter(ModelRelease.company_id == company_id)
            .filter(ModelRelease.catalog_key.isnot(None))
            .all()
        )
        for r in catalog_rows:
            r.is_flagship = False
        dated = [r for r in catalog_rows if r.release_date]
        if dated:
            max(dated, key=lambda r: r.release_date).is_flagship = True

    session.commit()
    return len(rows)
