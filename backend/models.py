from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, relationship


def utcnow():
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    metadata = MetaData(schema="ai_news")


class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    type = Column(String(30), nullable=False)  # rss | newsapi | reddit | hn | hf
    url = Column(Text, nullable=False)
    category = Column(String(50))  # news | models | papers | community
    enabled = Column(Integer, nullable=False, default=1)


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    slug = Column(String(200), nullable=False, unique=True)
    logo_url = Column(Text)
    description = Column(Text)

    model_releases = relationship("ModelRelease", back_populates="company")


class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey("sources.id"))
    title = Column(Text, nullable=False)
    url = Column(Text, nullable=False, unique=True)
    author = Column(Text)
    published_at = Column(DateTime(timezone=True))
    fetched_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    raw_summary = Column(Text)
    ai_summary = Column(Text)
    image_url = Column(Text)
    section = Column(String(30), default="news")  # models | companies | news | papers
    companies = Column(JSONB, default=list)  # list[str] slugs/names
    models = Column(JSONB, default=list)  # list[str] model names
    topics = Column(JSONB, default=list)  # list[str] topic tags
    score = Column(Integer, default=0)

    source = relationship("Source")


class ModelRelease(Base):
    __tablename__ = "model_releases"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id"))
    model_name = Column(String(200), nullable=False)
    release_date = Column(DateTime(timezone=True))
    description = Column(Text)
    benchmark_links = Column(JSONB, default=list)
    source_article_id = Column(Integer, ForeignKey("articles.id"))
    is_flagship = Column(Boolean, nullable=False, default=False)

    # Live catalog fields, populated from the OpenRouter models API. catalog_key
    # is the OpenRouter model id and the upsert key; it's NULL on the older
    # article-derived rows.
    catalog_key = Column(String(200))
    version_label = Column(String(200))
    context_length = Column(Integer)
    input_price = Column(Float)  # USD per 1M input tokens
    output_price = Column(Float)  # USD per 1M output tokens
    modalities = Column(JSONB, default=list)
    knowledge_cutoff = Column(String(50))
    reference_url = Column(Text)

    # Independent quality score from the Artificial Analysis API (0-100 composite
    # intelligence index), matched onto the catalog by model name. NULL when AA is
    # disabled or the model isn't ranked by AA.
    intelligence_index = Column(Float)

    company = relationship("Company", back_populates="model_releases")


class Pioneer(Base):
    __tablename__ = "pioneers"

    id = Column(Integer, primary_key=True)
    slug = Column(String(200), nullable=False, unique=True)
    name = Column(String(200), nullable=False)
    role = Column(String(300))
    company_name = Column(String(200))
    contribution = Column(Text)
    bio = Column(Text)
    photo_url = Column(Text)
    links = Column(JSONB, default=list)  # list[{"label": str, "url": str}]
    sort_order = Column(Integer, nullable=False, default=0)


class LeaderboardEntry(Base):
    __tablename__ = "leaderboard_entries"

    id = Column(Integer, primary_key=True)
    source = Column(String(50), nullable=False)  # e.g. "hf-open-llm"
    rank = Column(Integer, nullable=False)
    model_name = Column(String(300), nullable=False)
    organization = Column(String(200))
    score = Column(Float)
    fetched_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)


class BenchmarkScore(Base):
    """One row per model, holding all three benchmark dimensions the panel
    ranks by. Regenerated wholesale each ingestion run (delete + insert) by
    ingestion/sources/benchmark_source.py, so it always reflects the latest
    generation rather than piling up history.
    """

    __tablename__ = "benchmark_scores"

    id = Column(Integer, primary_key=True)
    model_name = Column(String(300), nullable=False)
    company = Column(String(200))
    intelligence = Column(Float)  # composite intelligence index, 0-100 (higher better)
    speed = Column(Float)  # median output tokens/sec (higher better)
    cost = Column(Float)  # USD for a standard task (lower better)
    # Per-category indices, 0-100 (higher better). Populated when the scoreboard
    # is sourced from the Artificial Analysis API; NULL for the grounded-LLM
    # fallback source, which only produces the composite intelligence score.
    coding = Column(Float)  # coding/software-engineering index
    math = Column(Float)  # math/quantitative-reasoning index
    agentic = Column(Float)  # agentic / tool-use index
    # True = open-weight model (Llama, Qwen, DeepSeek, ...), False = closed/API-only
    # (GPT, Claude, Gemini, ...). NULL only if classification genuinely couldn't be
    # determined. Powers the Leaderboard page's Open/Closed tabs.
    is_open_weights = Column(Boolean)
    source_note = Column(Text)  # e.g. "Artificial Analysis, 2026-09-10"
    generated_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"

    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey("sources.id"))
    started_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    finished_at = Column(DateTime(timezone=True))
    status = Column(String(20))  # running | ok | error
    items_found = Column(Integer, default=0)
    items_new = Column(Integer, default=0)
    error = Column(Text)
