-- Enrich model_releases into a real, live model catalog sourced from the
-- OpenRouter models API (free, no key). These columns are all nullable so
-- existing article-derived rows (catalog_key IS NULL) are unaffected.
--
-- catalog_key is the OpenRouter model id (e.g. "anthropic/claude-opus-5") and
-- is the upsert key for catalog rows, so a refresh updates in place instead of
-- piling up duplicates.

-- Schema is fully qualified (not via SET search_path) because a connection
-- pooler may not carry the search_path across statements, which would send
-- these ALTERs to a stale public.model_releases instead.

ALTER TABLE ai_news.model_releases ADD COLUMN IF NOT EXISTS catalog_key      VARCHAR(200);
ALTER TABLE ai_news.model_releases ADD COLUMN IF NOT EXISTS version_label    VARCHAR(200);
ALTER TABLE ai_news.model_releases ADD COLUMN IF NOT EXISTS context_length   INTEGER;
ALTER TABLE ai_news.model_releases ADD COLUMN IF NOT EXISTS input_price      DOUBLE PRECISION;  -- USD per 1M input tokens
ALTER TABLE ai_news.model_releases ADD COLUMN IF NOT EXISTS output_price     DOUBLE PRECISION;  -- USD per 1M output tokens
ALTER TABLE ai_news.model_releases ADD COLUMN IF NOT EXISTS modalities       JSONB DEFAULT '[]'::jsonb;
ALTER TABLE ai_news.model_releases ADD COLUMN IF NOT EXISTS knowledge_cutoff VARCHAR(50);
ALTER TABLE ai_news.model_releases ADD COLUMN IF NOT EXISTS reference_url    TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS ux_model_releases_catalog_key
    ON ai_news.model_releases (catalog_key) WHERE catalog_key IS NOT NULL;
