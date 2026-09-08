"""NewsAPI.org query for broader AI industry coverage. No-ops if NEWSAPI_KEY
is unset — this source is optional.

The free NewsAPI tier is capped at 100 requests/day. This module makes at
most one request per call, but ingestion can run every 15-30 minutes, so a
file-based throttle skips the call (returning []) if we've queried within
THROTTLE_MINUTES — keeping worst-case usage well under the daily cap even
with frequent cron runs plus ad-hoc manual runs during testing.
"""

import time
from datetime import datetime, timezone
from pathlib import Path

import requests

from config import Config

API = "https://newsapi.org/v2/everything"

# "everything" full-text-searches article bodies, which is how vaguely
# AI-adjacent noise (sports recaps, PyPI package listings, tabloid stories
# that mention "AI" once) got in. qInTitle requires the match in the
# headline itself — much higher precision.
QUERY = (
    '"artificial intelligence" OR OpenAI OR Anthropic OR "Google DeepMind" '
    'OR "large language model" OR LLM OR ChatGPT OR Gemini OR Claude'
)

# Restrict to reputable outlets so free-tier syndication/aggregator noise
# (Biztoc, Onefootball, random regional tabloids picking up wire stories)
# doesn't drown out real coverage. NewsAPI's `domains` param caps at 500 chars.
DOMAINS = ",".join(
    [
        "techcrunch.com",
        "theverge.com",
        "arstechnica.com",
        "wired.com",
        "venturebeat.com",
        "technologyreview.com",
        "reuters.com",
        "bloomberg.com",
        "cnbc.com",
        "theguardian.com",
        "engadget.com",
        "axios.com",
        "businessinsider.com",
        "forbes.com",
    ]
)

THROTTLE_MINUTES = 55
_STATE_FILE = Path(__file__).resolve().parent.parent.parent / "data" / ".newsapi_last_call"


def _throttled() -> bool:
    try:
        last_call = float(_STATE_FILE.read_text().strip())
    except (FileNotFoundError, ValueError):
        return False
    return (time.time() - last_call) < THROTTLE_MINUTES * 60


def _mark_called() -> None:
    _STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    _STATE_FILE.write_text(str(time.time()))


def fetch_all() -> list[dict]:
    if not Config.NEWSAPI_KEY or _throttled():
        return []
    resp = requests.get(
        API,
        params={
            "qInTitle": QUERY,
            "domains": DOMAINS,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": 50,
            "apiKey": Config.NEWSAPI_KEY,
        },
        timeout=15,
    )
    _mark_called()
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
