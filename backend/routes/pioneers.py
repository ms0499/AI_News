from flask import Blueprint, jsonify

from models import Pioneer
from services.db import get_session
from services.serialize import pioneer_to_dict

bp = Blueprint("pioneers", __name__)


@bp.get("/api/pioneers")
def list_pioneers():
    session = get_session()
    try:
        pioneers = session.query(Pioneer).order_by(Pioneer.sort_order).all()
        return jsonify({"pioneers": [pioneer_to_dict(p) for p in pioneers]})
    finally:
        session.close()
