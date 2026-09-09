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
