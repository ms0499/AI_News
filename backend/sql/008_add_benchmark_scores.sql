-- Adds the benchmark_scores table backing the "Model Benchmarks" panel on the
-- news page (intelligence / speed / cost). Mirrors backend/models.py — keep the
-- two in sync. Populated by ingestion/sources/benchmark_source.py.

CREATE TABLE IF NOT EXISTS ai_news.benchmark_scores (
    id            INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    model_name    VARCHAR(300) NOT NULL,
    company       VARCHAR(200),
    intelligence  DOUBLE PRECISION,   -- composite index 0-100 (higher better)
    speed         DOUBLE PRECISION,   -- output tokens/sec (higher better)
    cost          DOUBLE PRECISION,   -- USD per standard task (lower better)
    source_note   TEXT,
    generated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
