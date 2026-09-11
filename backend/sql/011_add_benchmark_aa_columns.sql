-- Adds the extra columns the Benchmarks page needs to mirror the
-- artificialanalysis.ai/models comparison table one-for-one: blended price
-- ($/M tokens), latency (median time-to-first-token, seconds), and context
-- window. Mirrors backend/models.py — keep the two in sync. Populated in
-- ingestion/sources/benchmark_source.py directly from the Artificial Analysis
-- Data API (pricing.price_1m_blended_3_to_1, median_time_to_first_token_seconds).
--
-- ADD ... IF NOT EXISTS so this migration is safe to re-run. Schema is fully
-- qualified because the NAS DB URI goes through a pgbouncer pooler that does not
-- carry `SET search_path` across statements (see sql/007 for the same gotcha).

ALTER TABLE ai_news.benchmark_scores
    ADD COLUMN IF NOT EXISTS price          DOUBLE PRECISION,  -- blended $/M tokens (3:1), as AA shows
    ADD COLUMN IF NOT EXISTS latency        DOUBLE PRECISION,  -- median time-to-first-token, seconds
    ADD COLUMN IF NOT EXISTS context_length INTEGER;           -- context window, tokens
