"""Hacker News stories matching AI keywords, via the public Algolia search API
(no key required)."""

import re
from datetime import datetime, timezone

import requests

QUERIES = ["AI", "LLM", "OpenAI", "Anthropic", "Gemini", "machine learning"]
API = "https://hn.algolia.com/api/v1/search_by_date"

# Algolia's search matches across a story's URL/author/text too, not just its
# title — so a query like "AI" pulls in stories whose title has nothing to do
# with AI (e.g. a random Show HN whose linked page happens to mention it
# once). Require the query term to actually appear in the title, as a whole
# word/phrase, before keeping an item.
_QUERY_PATTERNS = [re.compile(r"\b" + re.escape(q) + r"\b", re.IGNORECASE) for q in QUERIES]


def _title_is_relevant(title: str) -> bool:
    return any(pattern.search(title) for pattern in _QUERY_PATTERNS)


def fetch(query: str) -> list[dict]:
    resp = requests.get(
        API,
        params={"query": query, "tags": "story", "hitsPerPage": 25},
        timeout=15,
    )
    resp.raise_for_status()
    items = []
    for hit in resp.json().get("hits", []):
        url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit['objectID']}"
        title = hit.get("title")
        if not title or not _title_is_relevant(title):
            continue
        items.append(
            {
                "title": title.strip(),
                "url": url.strip(),
                "author": hit.get("author"),
                "published_at": datetime.fromtimestamp(
                    hit["created_at_i"], tz=timezone.utc
                ) if hit.get("created_at_i") else None,
                "raw_summary": "",
                "source_name": "Hacker News",
            }
        )
    return items


def fetch_all() -> list[dict]:
    items = []
    for query in QUERIES:
        try:
            items.extend(fetch(query))
        except requests.RequestException:
            continue
    return items
