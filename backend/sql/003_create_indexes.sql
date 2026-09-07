-- Run third (after 002_create_tables.sql). Supports the query patterns in
-- backend/routes/feed.py, models_tracker.py, companies.py.

CREATE INDEX IF NOT EXISTS idx_articles_section
    ON ai_news.articles (section);

CREATE INDEX IF NOT EXISTS idx_articles_published_at
    ON ai_news.articles (published_at DESC);

CREATE INDEX IF NOT EXISTS idx_articles_companies_gin
    ON ai_news.articles USING GIN (companies);

CREATE INDEX IF NOT EXISTS idx_articles_topics_gin
    ON ai_news.articles USING GIN (topics);

CREATE INDEX IF NOT EXISTS idx_model_releases_company_id
    ON ai_news.model_releases (company_id);

CREATE INDEX IF NOT EXISTS idx_model_releases_release_date
    ON ai_news.model_releases (release_date DESC);

CREATE INDEX IF NOT EXISTS idx_ingestion_runs_source_id
    ON ai_news.ingestion_runs (source_id);
