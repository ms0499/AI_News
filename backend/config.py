import os

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))


class Config:
    DB_URI = os.environ.get("AI_NEWS_DB_URI") or os.environ.get("DATABASE_URL")
    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")
    PORT = int(os.environ.get("PORT", 8010))
    CORS_ORIGIN = os.environ.get("CORS_ORIGIN", "http://localhost:5173")

    AI_SUMMARIZE_ENABLED = os.environ.get("AI_SUMMARIZE_ENABLED", "true").lower() == "true"
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

    NEWSAPI_KEY = os.environ.get("NEWSAPI_KEY")


if not Config.DB_URI:
    raise RuntimeError(
        "AI_NEWS_DB_URI (or DATABASE_URL) must be set — see backend/.env.example"
    )
