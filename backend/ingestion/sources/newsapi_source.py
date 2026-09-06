"""NewsAPI.org query for broader AI industry coverage. No-ops if NEWSAPI_KEY
is unset — this source is optional."""

from datetime import datetime, timezone

import requests

from config import Config

API = "https://newsapi.org/v2/everything"
QUERY = (
    '"artificial intelligence" OR OpenAI OR Anthropic OR "Google DeepMind" '
    'OR "large language model" OR LLM'
)


def fetch_all() -> list[dict]:
    if not Config.NEWSAPI_KEY:
        return []
    resp = requests.get(
        API,
        params={
            "q": QUERY,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": 50,
            "apiKey": Config.NEWSAPI_KEY,
        },
        timeout=15,
    )
    resp.raise_for_status()
    items = []
    for article in resp.json().get("articles", []):
        title = article.get("title")
        url = article.get("url")
        if not title or not url:
            continue
        published_at = None
        if article.get("publishedAt"):
            published_at = datetime.fromisoformat(
                article["publishedAt"].replace("Z", "+00:00")
            ).astimezone(timezone.utc)
        items.append(
            {
                "title": title.strip(),
                "url": url.strip(),
                "author": article.get("author"),
                "published_at": published_at,
                "raw_summary": (article.get("description") or "")[:2000],
                "source_name": (article.get("source") or {}).get("name", "NewsAPI"),
                "image_url": article.get("urlToImage"),
            }
        )
    return items
