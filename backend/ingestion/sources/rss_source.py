"""Curated RSS feeds from AI labs, companies, and publications."""

from datetime import datetime, timezone

import feedparser

FEEDS = [
    ("OpenAI", "https://openai.com/news/rss.xml"),
    ("Anthropic", "https://www.anthropic.com/rss.xml"),
    ("Google DeepMind", "https://deepmind.google/blog/rss.xml"),
    ("Hugging Face", "https://huggingface.co/blog/feed.xml"),
    ("Mistral AI", "https://mistral.ai/news/rss.xml"),
    ("TechCrunch AI", "https://techcrunch.com/category/artificial-intelligence/feed/"),
    ("The Verge AI", "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"),
    ("VentureBeat AI", "https://venturebeat.com/category/ai/feed/"),
    ("MIT Tech Review AI", "https://www.technologyreview.com/topic/artificial-intelligence/feed"),
    ("arXiv cs.AI", "http://export.arxiv.org/rss/cs.AI"),
    ("arXiv cs.LG", "http://export.arxiv.org/rss/cs.LG"),
]


def _parse_published(entry) -> datetime | None:
    for key in ("published_parsed", "updated_parsed"):
        value = entry.get(key)
        if value:
            return datetime(*value[:6], tzinfo=timezone.utc)
    return None


def fetch(feed_name: str, feed_url: str) -> list[dict]:
    parsed = feedparser.parse(feed_url)
    items = []
    for entry in parsed.entries:
        url = entry.get("link")
        title = entry.get("title")
        if not url or not title:
            continue
        items.append(
            {
                "title": title.strip(),
                "url": url.strip(),
                "author": entry.get("author"),
                "published_at": _parse_published(entry),
                "raw_summary": (entry.get("summary") or "").strip()[:2000],
                "source_name": feed_name,
            }
        )
    return items


def fetch_all() -> list[dict]:
    items = []
    for feed_name, feed_url in FEEDS:
        items.extend(fetch(feed_name, feed_url))
    return items
