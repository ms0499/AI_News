-- Adds the open-vs-closed classification backing the Leaderboard page's
-- Open Models / Closed Models tabs. Mirrors backend/models.py — keep in sync.
--
-- Populated in ingestion/sources/benchmark_source.py: read directly from the
-- Artificial Analysis API when available (Pro-tier "licensing.is_open_weights"
-- field), otherwise derived from a company/model-name heuristic.
--
-- ADD is IF NOT EXISTS so this migration is safe to re-run.

ALTER TABLE ai_news.benchmark_scores
    ADD COLUMN IF NOT EXISTS is_open_weights BOOLEAN;
