"""Top posts from AI-focused subreddits, via Reddit's public JSON endpoint
(no OAuth needed for read-only access to public listings)."""

from datetime import datetime, timezone

import requests

SUBREDDITS = ["MachineLearning", "LocalLLaMA", "singularity", "artificial"]
HEADERS = {"User-Agent": "AI_News/1.0 (personal news dashboard)"}


def fetch(subreddit: str) -> list[dict]:
    url = f"https://www.reddit.com/r/{subreddit}/top.json"
    resp = requests.get(url, params={"limit": 25, "t": "day"}, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    items = []
    for child in resp.json().get("data", {}).get("children", []):
        post = child.get("data", {})
        title = post.get("title")
        if not title or post.get("stickied"):
            continue
        permalink = post.get("permalink")
        external_url = post.get("url", "")
        # Prefer the Reddit discussion link for self-posts, the external link otherwise.
        link = external_url if external_url and not post.get("is_self") else f"https://reddit.com{permalink}"
        items.append(
            {
                "title": title.strip(),
                "url": link.strip(),
                "author": post.get("author"),
                "published_at": datetime.fromtimestamp(
                    post["created_utc"], tz=timezone.utc
                ) if post.get("created_utc") else None,
                "raw_summary": (post.get("selftext") or "")[:2000],
                "source_name": f"r/{subreddit}",
            }
        )
    return items


def fetch_all() -> list[dict]:
    items = []
    for subreddit in SUBREDDITS:
        try:
            items.extend(fetch(subreddit))
        except requests.RequestException:
            continue
    return items
