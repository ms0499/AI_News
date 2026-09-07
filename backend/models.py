from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
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
    author = Column(String(200))
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

    company = relationship("Company", back_populates="model_releases")


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
