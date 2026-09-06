# AI News

A dashboard for what's happening in AI right now — model releases, company moves, research,
and general news — pulled from RSS feeds, Hacker News, Hugging Face, and (optionally) NewsAPI
and Reddit, on a scheduled ingestion job, into Postgres.

Same overall shape as `Stock_Analysis`: Flask + PostgreSQL backend, Vite + React + TypeScript
frontend.

## Structure

- `backend/` — Flask API, SQLAlchemy models, and the ingestion pipeline (`backend/ingestion/`)
- `frontend/` — Vite + React + TS single-page app (Feed / Models / Companies)

## Local setup

### 1. Database

Create a Postgres database (local for dev, or your NAS instance for real use):

```bash
createdb ai_news
```

### 2. Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then edit .env: AI_NEWS_DB_URI at minimum
python app.py           # serves the API + (if built) the frontend on :8010
```

### 3. Ingest some data

```bash
cd backend
source .venv/bin/activate
python -m ingestion.run_ingestion
```

Run this on a schedule (cron/launchd, every 15-30 min) in production — the web app only ever
reads from Postgres, it never fetches sources live.

### 4. Frontend (dev mode, hot reload)

```bash
cd frontend
npm install
npm run dev   # http://localhost:5173, proxies /api to the backend on :8010
```

For a production-style single-process run, `npm run build` in `frontend/` and just hit
`http://localhost:8010` — Flask serves the built SPA directly.

## Notes / known limitations

- **Reddit**: the public unauthenticated JSON endpoint (`reddit.com/r/*/top.json`) is currently
  blocked from most IPs (returns a login wall). The source is wired up and fails gracefully —
  if you want real Reddit coverage, register a Reddit "script" app and switch
  `ingestion/sources/reddit_source.py` to OAuth (e.g. via `praw`).
- **NewsAPI**: optional; set `NEWSAPI_KEY` in `.env` to enable it. Free tier is rate-limited.
- **AI summarization/tagging**: optional; set `GEMINI_API_KEY` in `.env` to enable it. Without
  it, articles fall back to rule-based keyword tagging (`ingestion/classify.py`) and the raw
  source summary — the app is fully usable either way.
- **Login/accounts**: intentionally not built yet. The DB schema has no `users` table; add one
  (Flask-Login + Postgres, same pattern as `Stock_Analysis/my_stock_app/routes/auth.py`) when
  you're ready for it.
