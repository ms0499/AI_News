-- Adds the columns backing the Artificial Analysis integration. Mirrors
-- backend/models.py — keep the two in sync.
--
--  * benchmark_scores gains per-category indices so the "Model Benchmarks" panel
--    can rank models by coding / math / agentic ability, not just a single
--    composite intelligence score. Populated by
--    ingestion/sources/artificial_analysis.py; left NULL by the grounded-LLM
--    fallback source (ingestion/sources/benchmark_source.py).
--  * model_releases gains a per-model intelligence score so the Models catalog
--    page can show and sort by real, independent quality data.
--
-- All ADDs are IF NOT EXISTS so this migration is safe to re-run.

ALTER TABLE ai_news.benchmark_scores
    ADD COLUMN IF NOT EXISTS coding   DOUBLE PRECISION,  -- coding index 0-100 (higher better)
    ADD COLUMN IF NOT EXISTS math     DOUBLE PRECISION,  -- math index 0-100 (higher better)
    ADD COLUMN IF NOT EXISTS agentic  DOUBLE PRECISION;  -- agentic/tool-use index 0-100 (higher better)

ALTER TABLE ai_news.model_releases
    ADD COLUMN IF NOT EXISTS intelligence_index DOUBLE PRECISION;  -- AA composite index 0-100
