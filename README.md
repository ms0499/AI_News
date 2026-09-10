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

Create a Postgres database (local for dev, or your NAS instance for real use), then run
the SQL files in [`backend/sql/`](backend/sql/) in order (001, 002, 003, and optionally 004)
— e.g. open them in DBeaver against that database and execute each one. They create the
`ai_news` schema and all tables/indexes; `backend/models.py` is pinned to that same schema,
so the app and the manually-created tables always agree.

```bash
createdb ai_news
```

The app can also create tables itself via `init_db()` (`Base.metadata.create_all`, idempotent —
harmless to run even if the SQL files already created everything), but the SQL files are the
source of truth to review/run by hand.

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

## Deploying on the NAS (ainews.damsm.com)

The Cloudflare tunnel **AI-News** is already created and its connector is already
running on the NAS, with `ainews.damsm.com` forwarding to `localhost:6001` (set up in
the Cloudflare Zero Trust dashboard, so there's no local `cloudflared.yml` to edit —
same idea as `stocks-tunnel`, just managed remotely). All that's left is to get the
app itself running on the NAS, listening on port 6001.

```bash
# 1) On the NAS: clone/pull the repo (adjust the path to wherever you keep web apps,
#    e.g. alongside Stock_Analysis at /volume1/web/)
cd /volume1/web
git clone https://github.com/ms0499/AI_News.git   # or: git -C AI_News pull
cd AI_News/backend

# 2) Python env + deps
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3) Configure .env — PORT=6001 is the important one (matches the tunnel's ingress)
cp .env.example .env
#   AI_NEWS_DB_URI=postgresql+pg8000://appuser:PASSWORD@localhost:5432/ai_news
#   PORT=6001
#   CORS_ORIGIN=https://ainews.damsm.com
#   (optionally) GEMINI_API_KEY / NEWSAPI_KEY

# 4) Create the database (separate from stock_app/STOCKS, same Postgres server),
#    then run backend/sql/001_create_schema.sql, 002_create_tables.sql, and
#    003_create_indexes.sql against it (e.g. via DBeaver) to create the ai_news
#    schema and tables.
createdb ai_news   # or: psql -c "CREATE DATABASE ai_news;"

# 5) Build the frontend (Flask serves this static bundle in production)
cd ../frontend
npm install
npm run build
cd ../backend

# 6) One-time: seed some data so the site isn't empty
source .venv/bin/activate
python -m ingestion.run_ingestion

# 7) Start the app under gunicorn, bound to port 6001 via .env.
#    Daemonizes on its own — the prompt returns immediately. Stop with ./stop_gunicorn.sh.
./run_gunicorn.sh
```

`ainews.damsm.com` should now serve the dashboard. If it doesn't come up, check that
the tunnel connector on the NAS shows as connected (`cloudflared tunnel info AI-News`
from any machine logged into that Cloudflare account) and that something is actually
listening on `127.0.0.1:6001` on the NAS (`curl localhost:6001/api/health`).

**Keep it running + fresh content:**
- Run `./run_gunicorn.sh` under whatever supervisor you use for Stock_Analysis on this
  NAS (systemd, a `@reboot` cron entry, or Synology's Task Scheduler as a boot-run
  script) so it survives a NAS reboot.
- Schedule `backend/run_ingestion.sh` every 15-30 minutes (NAS Task Scheduler: User-defined
  script, or a crontab entry like `*/20 * * * * /volume1/web/AI_News/backend/run_ingestion.sh`)
  to keep the feed updated — the web app only ever reads from Postgres, it never fetches
  sources live.

## Notes / known limitations

- **Reddit**: the public unauthenticated JSON endpoint (`reddit.com/r/*/top.json`) is currently
  blocked from most IPs (returns a login wall). The source is wired up and fails gracefully —
  if you want real Reddit coverage, register a Reddit "script" app and switch
  `ingestion/sources/reddit_source.py` to OAuth (e.g. via `praw`).
- **Features tab**: sourced from company blogs already in `ingestion/sources/rss_source.py`'s RSS
  list. Anthropic and Mistral AI's feed URLs there currently 404 (no working public RSS found for
  either) — the source fails gracefully, same as Reddit below, so Features content is limited to
  OpenAI, Google DeepMind, and Hugging Face until working feeds are found.
- **Leaderboard page**: pulls Hugging Face's archived "Open LLM Leaderboard" (v2) dataset — real,
  free, live data, but it ranks community fine-tunes/merges of open-weight models, not frontier
  closed models (it will never show GPT/Gemini/Claude). Treat it as a secondary "what's trending
  in the open-weight community" view; the flagship badge on the Models page (curated in
  `backend/data/curated_models.py`) is the answer to "what's the best model right now."
- **Artificial Analysis**: optional; set `AA_API_KEY` in `.env` (get one at
  https://artificialanalysis.ai/data-api) to power the "Model Benchmarks" panel with real,
  independently-measured data instead of the grounded-LLM guess. When set, it becomes the
  preferred benchmark source — the panel gains **Coding / Math / Agentic** category leaderboards
  (alongside Intelligence / Speed / Cost), and the Models page shows each model's Artificial
  Analysis Intelligence Index (★). The scoreboard + catalog scores refresh from the ~daily
  `python -m ingestion.run_benchmarks` job; without a key the site falls back to the existing
  LLM benchmark source and the OpenRouter catalog, unchanged.
- **NewsAPI**: optional; set `NEWSAPI_KEY` in `.env` to enable it. Free tier is rate-limited.
- **AI summarization/tagging**: optional; set `GEMINI_API_KEY` in `.env` to enable it. Without
  it, articles fall back to rule-based keyword tagging (`ingestion/classify.py`) and the raw
  source summary — the app is fully usable either way.
- **Login/accounts**: intentionally not built yet. The DB schema has no `users` table; add one
  (Flask-Login + Postgres, same pattern as `Stock_Analysis/my_stock_app/routes/auth.py`) when
  you're ready for it.
