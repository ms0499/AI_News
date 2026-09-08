"""General VC/funding news feeds, filtered down to AI-relevant items.

Unlike rss_source.py's feeds (which are AI-specific by choice of publication),
TechCrunch's Venture category and Crunchbase News cover every sector — so
every item is checked against an AI keyword list here before being returned.
Matching items still flow through the normal classify() pipeline in
run_ingestion.py, which tags them section="funding" via the existing
"funding" topic keywords (raises, series a/b/c, valuation, ...).
"""

from ingestion.classify import COMPANY_KEYWORDS, MODEL_TO_COMPANY
from ingestion.sources.rss_source import fetch

FEEDS = [
    ("TechCrunch Venture", "https://techcrunch.com/category/venture/feed/"),
    ("Crunchbase News", "https://news.crunchbase.com/feed/"),
]

GENERIC_AI_TERMS = [
    "artificial intelligence",
    "generative ai",
    "genai",
    " ai ",
    " ai-",
    "-ai ",
    "large language model",
    "llm",
    "foundation model",
    "machine learning",
]

_AI_KEYWORDS = (
    [kw for kws in COMPANY_KEYWORDS.values() for kw in kws]
    + list(MODEL_TO_COMPANY)
    + GENERIC_AI_TERMS
)


def _is_ai_related(item: dict) -> bool:
    text = f" {item['title']} {item.get('raw_summary', '')} ".lower()
    return any(kw in text for kw in _AI_KEYWORDS)


def fetch_all() -> list[dict]:
    items = []
    for feed_name, feed_url in FEEDS:
        items.extend(item for item in fetch(feed_name, feed_url) if _is_ai_related(item))
    return items
