from flask import Blueprint, jsonify, request

from models import Company, ModelRelease
from services.db import get_session
from services.serialize import model_release_to_dict

bp = Blueprint("models_tracker", __name__)


@bp.get("/api/models")
def get_model_releases():
    company_slug = request.args.get("company")
    catalog_only = request.args.get("catalog") in ("1", "true", "yes")

    session = get_session()
    try:
        query = session.query(ModelRelease).join(Company)
        if company_slug:
            query = query.filter(Company.slug == company_slug)
        if catalog_only:
            query = query.filter(ModelRelease.catalog_key.isnot(None))
        releases = query.order_by(ModelRelease.release_date.desc().nullslast()).all()

        payload = [model_release_to_dict(r) for r in releases]

        # Group by company (newest first within each) so the frontend can render
        # per-company sections without re-sorting, plus a flat list for a
        # cross-company "latest releases" timeline.
        groups: dict[str, dict] = {}
        for r in payload:
            slug = r["company_slug"] or "unknown"
            g = groups.setdefault(
                slug,
                {"company": r["company"], "company_slug": slug, "models": []},
            )
            g["models"].append(r)
        group_list = sorted(
            groups.values(),
            key=lambda g: (g["models"][0]["release_date"] or ""),
            reverse=True,
        )

        return jsonify({"releases": payload, "groups": group_list})
    finally:
        session.close()
