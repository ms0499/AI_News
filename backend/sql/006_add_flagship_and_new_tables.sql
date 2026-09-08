-- Adds the flagship-model flag plus the pioneers and leaderboard_entries
-- tables. Mirrors backend/models.py — keep the two in sync.

ALTER TABLE ai_news.model_releases
    ADD COLUMN IF NOT EXISTS is_flagship BOOLEAN NOT NULL DEFAULT false;

CREATE TABLE IF NOT EXISTS ai_news.pioneers (
    id            INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    slug          VARCHAR(200) NOT NULL UNIQUE,
    name          VARCHAR(200) NOT NULL,
    role          VARCHAR(300),
    company_name  VARCHAR(200),
    contribution  TEXT,
    bio           TEXT,
    photo_url     TEXT,
    links         JSONB NOT NULL DEFAULT '[]'::jsonb,
    sort_order    INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS ai_news.leaderboard_entries (
    id           INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source       VARCHAR(50) NOT NULL,
    rank         INTEGER NOT NULL,
    model_name   VARCHAR(300) NOT NULL,
    organization VARCHAR(200),
    score        DOUBLE PRECISION,
    fetched_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_pioneers_sort_order
    ON ai_news.pioneers (sort_order);

CREATE INDEX IF NOT EXISTS idx_leaderboard_entries_source_rank
    ON ai_news.leaderboard_entries (source, rank);
