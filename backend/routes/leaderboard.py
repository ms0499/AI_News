from flask import Blueprint, jsonify, request

from models import LeaderboardEntry
from services.db import get_session
from services.serialize import leaderboard_entry_to_dict

bp = Blueprint("leaderboard", __name__)


@bp.get("/api/leaderboard")
def list_leaderboard():
    source = request.args.get("source", "hf-trending")

    session = get_session()
    try:
        entries = (
            session.query(LeaderboardEntry)
            .filter_by(source=source)
            .order_by(LeaderboardEntry.rank)
            .all()
        )
        return jsonify({"source": source, "entries": [leaderboard_entry_to_dict(e) for e in entries]})
    finally:
        session.close()
