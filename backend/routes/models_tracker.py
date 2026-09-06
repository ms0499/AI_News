from flask import Blueprint, jsonify, request

from models import Company, ModelRelease
from services.db import get_session
from services.serialize import model_release_to_dict

bp = Blueprint("models_tracker", __name__)


@bp.get("/api/models")
def get_model_releases():
    company_slug = request.args.get("company")

    session = get_session()
    try:
        query = session.query(ModelRelease).join(Company)
        if company_slug:
            query = query.filter(Company.slug == company_slug)
        releases = query.order_by(ModelRelease.release_date.desc().nullslast()).all()
        return jsonify({"releases": [model_release_to_dict(r) for r in releases]})
    finally:
        session.close()
