"""Hugging Face daily papers + trending models — a dedicated feed for the
Models section, separate from general news."""

from datetime import datetime, timezone

import requests

PAPERS_API = "https://huggingface.co/api/daily_papers"
MODELS_API = "https://huggingface.co/api/models"


def fetch_daily_papers() -> list[dict]:
    resp = requests.get(PAPERS_API, timeout=15)
    resp.raise_for_status()
    items = []
    for entry in resp.json():
        paper = entry.get("paper", {})
        title = paper.get("title")
        paper_id = paper.get("id")
        if not title or not paper_id:
            continue
        items.append(
            {
                "title": title.strip(),
                "url": f"https://huggingface.co/papers/{paper_id}",
                "author": None,
                "published_at": datetime.fromisoformat(
                    entry["publishedAt"].replace("Z", "+00:00")
                ).astimezone(timezone.utc) if entry.get("publishedAt") else None,
                "raw_summary": (paper.get("summary") or "")[:2000],
                "source_name": "Hugging Face Daily Papers",
                "section": "papers",
            }
        )
    return items


MIN_LIKES_7D = 50


def fetch_trending_models() -> list[dict]:
    resp = requests.get(
        MODELS_API,
        params={"sort": "likes7d", "direction": -1, "limit": 30},
        timeout=15,
    )
    resp.raise_for_status()
    items = []
    for model in resp.json():
        model_id = model.get("id") or model.get("modelId")
        if not model_id or (model.get("likes") or 0) < MIN_LIKES_7D:
            continue
        items.append(
            {
                "title": f"New model: {model_id}",
                "url": f"https://huggingface.co/{model_id}",
                "author": model_id.split("/")[0] if "/" in model_id else None,
                "published_at": datetime.fromisoformat(
                    model["createdAt"].replace("Z", "+00:00")
                ).astimezone(timezone.utc) if model.get("createdAt") else None,
                "raw_summary": f"Tags: {', '.join(model.get('tags', [])[:8])}",
                "source_name": "Hugging Face Models",
                "section": "models",
            }
        )
    return items


def fetch_all() -> list[dict]:
    items = []
    try:
        items.extend(fetch_daily_papers())
    except requests.RequestException:
        pass
    try:
        items.extend(fetch_trending_models())
    except requests.RequestException:
        pass
    return items
