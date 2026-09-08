from collections import defaultdict, deque

from flask import Blueprint, jsonify, request

from models import Article
from services.db import get_session
from services.serialize import article_to_dict

bp = Blueprint("feed", __name__)

PAGE_SIZE = 30

# How many of the most-recent articles to pull before diversifying. Wide
# enough to round-robin several pages deep without re-querying per page.
DIVERSITY_POOL_SIZE = PAGE_SIZE * 10


def _diversify(articles: list[Article]) -> list[Article]:
    """Round-robin articles by source, preserving each source's own recency
    order, so one prolific source (a company's blog backlog, or a fast-moving
    aggregator) can't fill an entire page just by publishing the most.
    """
    buckets: dict[int, deque] = defaultdict(deque)
    order: list[int] = []
    for article in articles:
        if article.source_id not in buckets:
            order.append(article.source_id)
        buckets[article.source_id].append(article)

    result = []
    while order:
        for source_id in list(order):
            result.append(buckets[source_id].popleft())
            if not buckets[source_id]:
                order.remove(source_id)
    return result


@bp.get("/api/feed")
def get_feed():
    section = request.args.get("section")
    company = request.args.get("company")
    topic = request.args.get("topic")
    page = max(int(request.args.get("page", 1)), 1)
    filtered = bool(section or company or topic)

    session = get_session()
    try:
        query = session.query(Article)
        if section:
            query = query.filter(Article.section == section)
        if company:
            query = query.filter(Article.companies.contains([company]))
        if topic:
            query = query.filter(Article.topics.contains([topic]))

        total = query.count()
        query = query.order_by(Article.published_at.desc().nullslast(), Article.fetched_at.desc())

        if filtered:
            articles = query.offset((page - 1) * PAGE_SIZE).limit(PAGE_SIZE).all()
        else:
            # The unfiltered "everything" feed gets diversified across
            # sources; a filtered view (one section/company/topic) stays
            # purely chronological since the user asked for that slice.
            pool = query.limit(max(page * PAGE_SIZE, DIVERSITY_POOL_SIZE)).all()
            diversified = _diversify(pool)
            articles = diversified[(page - 1) * PAGE_SIZE : page * PAGE_SIZE]

        return jsonify(
            {
                "articles": [article_to_dict(a) for a in articles],
                "page": page,
                "page_size": PAGE_SIZE,
                "total": total,
            }
        )
    finally:
        session.close()
