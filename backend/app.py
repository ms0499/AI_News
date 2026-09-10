import os

from flask import Flask, send_from_directory
from flask_cors import CORS

from config import Config
from routes import (
    admin,
    benchmarks,
    companies,
    feed,
    health,
    leaderboard,
    models_tracker,
    pioneers,
)
from services.db import init_db

FRONTEND_DIST = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")


def create_app() -> Flask:
    # static_folder=None disables Flask's auto-registered static route, which
    # would otherwise shadow the catch-all below and 404 on any SPA client-side
    # route (e.g. /models) instead of falling through to serve index.html.
    app = Flask(__name__, static_folder=None)
    app.config["SECRET_KEY"] = Config.SECRET_KEY

    CORS(app, resources={r"/api/*": {"origins": Config.CORS_ORIGIN}})

    for bp in (health.bp, feed.bp, models_tracker.bp, companies.bp, pioneers.bp, leaderboard.bp, benchmarks.bp, admin.bp):
        app.register_blueprint(bp)

    @app.get("/")
    @app.get("/<path:path>")
    def serve_spa(path: str = ""):
        full_path = os.path.join(FRONTEND_DIST, path)
        if path and os.path.isfile(full_path):
            return send_from_directory(FRONTEND_DIST, path)
        return send_from_directory(FRONTEND_DIST, "index.html")

    with app.app_context():
        init_db()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=Config.PORT, debug=True)
