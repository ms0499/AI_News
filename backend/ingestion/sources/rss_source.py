"""Curated RSS feeds from AI labs, companies, and publications."""

from datetime import datetime, timezone

import feedparser

# Google News RSS search is a free, no-key fallback for labs that don't publish
# a working official feed (Anthropic's is dead; Meta and xAI have none). These
# carry third-party coverage, so they're deliberately NOT treated as official
# company blogs in classify.py — company/model attribution comes from keywords.
def _google_news(query: str) -> str:
    from urllib.parse import quote

    return f"https://news.google.com/rss/search?q={quote(query)}&hl=en-US&gl=US&ceid=US:en"


FEEDS = [
    # --- Official lab blogs (first-party) ---
    ("OpenAI", "https://openai.com/news/rss.xml"),
    ("Google DeepMind", "https://deepmind.google/blog/rss.xml"),
    ("Hugging Face", "https://huggingface.co/blog/feed.xml"),
    ("Mistral AI", "https://mistral.ai/rss.xml"),
    ("AWS Machine Learning", "https://aws.amazon.com/blogs/machine-learning/feed/"),
    ("Nvidia Blog", "https://blogs.nvidia.com/feed/"),
    ("Microsoft Research", "https://www.microsoft.com/en-us/research/feed/"),
    # --- Reputable AI publications ---
    ("TechCrunch AI", "https://techcrunch.com/category/artificial-intelligence/feed/"),
    ("The Verge AI", "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"),
    ("VentureBeat AI", "https://venturebeat.com/category/ai/feed/"),
    ("MIT Tech Review AI", "https://www.technologyreview.com/topic/artificial-intelligence/feed"),
    ("Ars Technica AI", "https://arstechnica.com/ai/feed/"),
    ("Simon Willison", "https://simonwillison.net/atom/everything/"),
    # --- Research ---
    ("arXiv cs.AI", "http://export.arxiv.org/rss/cs.AI"),
    ("arXiv cs.LG", "http://export.arxiv.org/rss/cs.LG"),
    # --- Google News fallbacks for labs without a working official feed ---
    ("Anthropic (news)", _google_news("Anthropic Claude when:14d")),
    ("Meta AI (news)", _google_news("Meta AI Llama model when:14d")),
    ("xAI (news)", _google_news("xAI Grok model when:14d")),
]


def _parse_published(entry) -> datetime | None:
    for key in ("published_parsed", "updated_parsed"):
        value = entry.get(key)
        if value:
            return datetime(*value[:6], tzinfo=timezone.utc)
    return None


def fetch(feed_name: str, feed_url: str) -> list[dict]:
    is_google_news = "news.google.com" in feed_url
    parsed = feedparser.parse(feed_url)
    items = []
    for entry in parsed.entries:
        url = entry.get("link")
        title = entry.get("title")
        if not url or not title:
            continue
        title = title.strip()
        raw_summary = (entry.get("summary") or "").strip()[:2000]
        if is_google_news:
            # Google News wraps every item in identical boilerplate that names
            # "Google" (polluting company tagging) and appends " - Publisher" to
            # the title. Drop the summary and strip the publisher suffix so
            # classification runs on the clean headline only.
            raw_summary = ""
            if " - " in title:
                title = title.rsplit(" - ", 1)[0].strip()
        items.append(
            {
                "title": title,
                "url": url.strip(),
                "author": entry.get("author"),
                "published_at": _parse_published(entry),
                "raw_summary": raw_summary,
                "source_name": feed_name,
            }
        )
    return items


def fetch_all() -> list[dict]:
    items = []
    for feed_name, feed_url in FEEDS:
        items.extend(fetch(feed_name, feed_url))
    return items
