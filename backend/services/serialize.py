from urllib.parse import urlparse


def _fallback_summary(article) -> str:
    """Some sources (Hacker News in particular) never carry a body/description.
    Rather than showing a bare title-only card, give the reader at least a
    one-line hint of where the story leads."""
    host = urlparse(article.url).netloc.removeprefix("www.")
    return f"Full story at {host} — tap through to read more." if host else "Tap through to read the full story."


def article_to_dict(article) -> dict:
    return {
        "id": article.id,
        "title": article.title,
        "url": article.url,
        "author": article.author,
        "published_at": article.published_at.isoformat() if article.published_at else None,
        "summary": article.ai_summary or article.raw_summary or _fallback_summary(article),
        "image_url": article.image_url,
        "section": article.section,
        "companies": article.companies or [],
        "models": article.models or [],
        "topics": article.topics or [],
        "source": article.source.name if article.source else None,
    }


def company_to_dict(company, recent_articles=None) -> dict:
    data = {
        "id": company.id,
        "name": company.name,
        "slug": company.slug,
        "logo_url": company.logo_url,
        "description": company.description,
    }
    if recent_articles is not None:
        data["recent_articles"] = [article_to_dict(a) for a in recent_articles]
    return data


def model_release_to_dict(release) -> dict:
    return {
        "id": release.id,
        "model_name": release.model_name,
        "release_date": release.release_date.isoformat() if release.release_date else None,
        "description": release.description,
        "benchmark_links": release.benchmark_links or [],
        "company": release.company.name if release.company else None,
        "company_slug": release.company.slug if release.company else None,
    }
