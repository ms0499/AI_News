from flask import Blueprint, jsonify, request

from models import Article
from services.db import get_session
from services.serialize import article_to_dict

bp = Blueprint("feed", __name__)

PAGE_SIZE = 30


@bp.get("/api/feed")
def get_feed():
    section = request.args.get("section")
    company = request.args.get("company")
    topic = request.args.get("topic")
    page = max(int(request.args.get("page", 1)), 1)

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
        articles = (
            query.order_by(Article.published_at.desc().nullslast(), Article.fetched_at.desc())
            .offset((page - 1) * PAGE_SIZE)
            .limit(PAGE_SIZE)
            .all()
        )
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
