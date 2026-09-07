-- arXiv entries can carry hundreds of co-authors, easily exceeding 200 chars.
-- Widen articles.author to TEXT to match title/url/raw_summary.
ALTER TABLE ai_news.articles ALTER COLUMN author TYPE TEXT;
