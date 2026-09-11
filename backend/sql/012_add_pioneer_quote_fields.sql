-- Adds a "latest quote" block to pioneers, so each card can surface a recent
-- real public statement/philosophy quote alongside the static bio. Mirrors
-- backend/models.py — keep the two in sync. Populated by hand in
-- data/curated_pioneers.py, same editorial-curation rationale as the rest of
-- the Pioneer fields (see that file's docstring).
--
-- ADD ... IF NOT EXISTS so this migration is safe to re-run. Schema is fully
-- qualified because the NAS DB URI goes through a pgbouncer pooler that does
-- not carry `SET search_path` across statements (see sql/007 for the same
-- gotcha).

ALTER TABLE ai_news.pioneers
    ADD COLUMN IF NOT EXISTS latest_quote        TEXT,
    ADD COLUMN IF NOT EXISTS quote_date           VARCHAR(50),
    ADD COLUMN IF NOT EXISTS quote_source_label   VARCHAR(200),
    ADD COLUMN IF NOT EXISTS quote_source_url     TEXT;
