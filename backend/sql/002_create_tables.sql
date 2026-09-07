-- Run second (after 001_create_schema.sql). Mirrors backend/models.py exactly —
-- keep the two in sync if the SQLAlchemy models change.
-- Tables are created in FK-dependency order.

CREATE TABLE IF NOT EXISTS ai_news.sources (
    id       INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name     VARCHAR(200) NOT NULL,
    type     VARCHAR(30)  NOT NULL,   -- rss | newsapi | reddit | hn | hf
    url      TEXT         NOT NULL,
    category VARCHAR(50),             -- news | models | papers | community
    enabled  INTEGER      NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS ai_news.companies (
    id          INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name        VARCHAR(200) NOT NULL,
    slug        VARCHAR(200) NOT NULL UNIQUE,
    logo_url    TEXT,
    description TEXT
);

CREATE TABLE IF NOT EXISTS ai_news.articles (
    id           INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_id    INTEGER REFERENCES ai_news.sources(id),
    title        TEXT         NOT NULL,
    url          TEXT         NOT NULL UNIQUE,
    author       TEXT,
    published_at TIMESTAMPTZ,
    fetched_at   TIMESTAMPTZ  NOT NULL DEFAULT now(),
    raw_summary  TEXT,
    ai_summary   TEXT,
    image_url    TEXT,
    section      VARCHAR(30)  DEFAULT 'news',  -- models | companies | news | papers
    companies    JSONB        DEFAULT '[]'::jsonb,  -- list[str] slugs/names
    models       JSONB        DEFAULT '[]'::jsonb,  -- list[str] model names
    topics       JSONB        DEFAULT '[]'::jsonb,  -- list[str] topic tags
    score        INTEGER      DEFAULT 0
);

CREATE TABLE IF NOT EXISTS ai_news.model_releases (
    id                 INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    company_id         INTEGER REFERENCES ai_news.companies(id),
    model_name         VARCHAR(200) NOT NULL,
    release_date       TIMESTAMPTZ,
    description        TEXT,
    benchmark_links    JSONB DEFAULT '[]'::jsonb,
    source_article_id  INTEGER REFERENCES ai_news.articles(id)
);

CREATE TABLE IF NOT EXISTS ai_news.ingestion_runs (
    id           INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_id    INTEGER REFERENCES ai_news.sources(id),
    started_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at  TIMESTAMPTZ,
    status       VARCHAR(20),   -- running | ok | error
    items_found  INTEGER DEFAULT 0,
    items_new    INTEGER DEFAULT 0,
    error        TEXT
);
