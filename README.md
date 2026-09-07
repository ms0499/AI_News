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
#   AI_NEWS_DB_URI=postgresql+psycopg2://appuser:PASSWORD@localhost:5432/ai_news
#   PORT=6001
#   CORS_ORIGIN=https://ainews.damsm.com
#   (optionally) GEMINI_API_KEY / NEWSAPI_KEY

# 4) Create the database (separate from stock_app/STOCKS, same Postgres server)
createdb ai_news   # or: psql -c "CREATE DATABASE ai_news;"

# 5) Build the frontend (Flask serves this static bundle in production)
cd ../frontend
npm install
npm run build
cd ../backend

# 6) One-time: seed some data so the site isn't empty
source .venv/bin/activate
python -m ingestion.run_ingestion

# 7) Start the app under gunicorn, bound to port 6001 via .env
./run_gunicorn.sh
# or detached: nohup ./run_gunicorn.sh > logs/gunicorn.out 2>&1 &
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
- **NewsAPI**: optional; set `NEWSAPI_KEY` in `.env` to enable it. Free tier is rate-limited.
- **AI summarization/tagging**: optional; set `GEMINI_API_KEY` in `.env` to enable it. Without
  it, articles fall back to rule-based keyword tagging (`ingestion/classify.py`) and the raw
  source summary — the app is fully usable either way.
- **Login/accounts**: intentionally not built yet. The DB schema has no `users` table; add one
  (Flask-Login + Postgres, same pattern as `Stock_Analysis/my_stock_app/routes/auth.py`) when
  you're ready for it.
