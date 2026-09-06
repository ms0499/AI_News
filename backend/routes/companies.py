from flask import Blueprint, abort, jsonify

from models import Article, Company
from services.db import get_session
from services.serialize import article_to_dict, company_to_dict

bp = Blueprint("companies", __name__)


@bp.get("/api/companies")
def list_companies():
    session = get_session()
    try:
        companies = session.query(Company).order_by(Company.name).all()
        return jsonify({"companies": [company_to_dict(c) for c in companies]})
    finally:
        session.close()


@bp.get("/api/companies/<slug>")
def get_company(slug: str):
    session = get_session()
    try:
        company = session.query(Company).filter_by(slug=slug).one_or_none()
        if company is None:
            abort(404)
        recent = (
            session.query(Article)
            .filter(Article.companies.contains([company.name]))
            .order_by(Article.published_at.desc().nullslast())
            .limit(20)
            .all()
        )
        return jsonify(
            {
                "company": company_to_dict(company),
                "recent_articles": [article_to_dict(a) for a in recent],
            }
        )
    finally:
        session.close()
