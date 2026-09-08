from flask import Blueprint, jsonify

from models import IngestionRun
from services.db import get_session

bp = Blueprint("admin", __name__)


@bp.get("/api/admin/ingestion-runs")
def list_ingestion_runs():
    session = get_session()
    try:
        runs = session.query(IngestionRun).order_by(IngestionRun.started_at.desc()).limit(50).all()
        return jsonify(
            {
                "runs": [
                    {
                        "id": r.id,
                        "started_at": r.started_at.isoformat() if r.started_at else None,
                        "finished_at": r.finished_at.isoformat() if r.finished_at else None,
                        "status": r.status,
                        "items_found": r.items_found,
                        "items_new": r.items_new,
                        "error": r.error,
                    }
                    for r in runs
                ]
            }
        )
    finally:
        session.close()


@bp.post("/api/admin/ingest")
def trigger_ingestion():
    from ingestion.run_ingestion import run

    run()
    return jsonify({"status": "started"})


@bp.post("/api/admin/seed-curated-models")
def seed_curated_models():
    from scripts.seed_curated_models import run

    result = run()
    return jsonify(result)
