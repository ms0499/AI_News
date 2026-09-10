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
    # Hard cap on Gemini summarize calls per ingestion run, so a surprise backlog
    # of new articles can never blow the free-tier daily quota in a single pass.
    # Articles past the cap are still ingested — they just keep their raw summary.
    AI_SUMMARIZE_MAX_PER_RUN = int(os.environ.get("AI_SUMMARIZE_MAX_PER_RUN", 100))

    # --- Benchmark scoreboard generation ---------------------------------------
    # Populates the "Model Benchmarks" panel. Preferred source is the Artificial
    # Analysis Data API (real measured intelligence/speed/price data, no LLM in the
    # loop); if no AA key is configured, it falls back to the LLM generator below.
    # Off by default.
    BENCHMARK_ENABLED = os.environ.get("BENCHMARK_ENABLED", "false").lower() == "true"
    # Artificial Analysis Data API key (free tier: 1,000 requests/day). Get one at
    # https://artificialanalysis.ai/insights. When set, this is the primary source
    # and no LLM/grounded generation request is made — the numbers are measured,
    # not a model's recollection, so they can't hallucinate or drift.
    ARTIFICIAL_ANALYSIS_API_KEY = os.environ.get("ARTIFICIAL_ANALYSIS_API_KEY")
    ARTIFICIAL_ANALYSIS_API_URL = os.environ.get(
        "ARTIFICIAL_ANALYSIS_API_URL",
        "https://artificialanalysis.ai/api/v2/data/llms/models",
    )
    # --- LLM fallback (used only when no Artificial Analysis key is set) ---------
    BENCHMARK_MODEL = os.environ.get("BENCHMARK_MODEL", "gemini-2.5-pro")
    # Its own key so the benchmark model can even be a different provider/project;
    # falls back to the summarizer's Gemini key when you reuse the same account.
    BENCHMARK_API_KEY = os.environ.get("BENCHMARK_API_KEY") or GEMINI_API_KEY
    # Enable Google Search grounding so the model answers from CURRENT standings
    # instead of stale training data. Strongly recommended — without it the scores
    # are the model's guess and will be out of date.
    BENCHMARK_USE_GROUNDING = (
        os.environ.get("BENCHMARK_USE_GROUNDING", "true").lower() == "true"
    )
    # How many models to rank in the panel.
    BENCHMARK_TOP_N = int(os.environ.get("BENCHMARK_TOP_N", 10))
    # Minimum hours between benchmark regenerations. The benchmark runs from its
    # own entrypoint (run_benchmarks.py), scheduled roughly once a day; this guard
    # makes that entrypoint a no-op if the table was refreshed more recently, so a
    # misfiring or too-frequent cron can't burn grounded API requests. Pass --force
    # to override. Benchmark standings barely move day-to-day, so ~20h is plenty.
    BENCHMARK_MIN_INTERVAL_HOURS = float(
        os.environ.get("BENCHMARK_MIN_INTERVAL_HOURS", 20)
    )
    # Per-request timeout (seconds) for the benchmark LLM call, so a stalled
    # endpoint raises DeadlineExceeded instead of hanging the cron forever.
    BENCHMARK_REQUEST_TIMEOUT = float(
        os.environ.get("BENCHMARK_REQUEST_TIMEOUT", 120)
    )

    NEWSAPI_KEY = os.environ.get("NEWSAPI_KEY")


if not Config.DB_URI:
    raise RuntimeError(
        "AI_NEWS_DB_URI (or DATABASE_URL) must be set — see backend/.env.example"
    )
