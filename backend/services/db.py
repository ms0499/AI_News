from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import Config
from models import Base

engine = create_engine(Config.DB_URI, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def init_db():
    Base.metadata.create_all(engine)


def get_session():
    return SessionLocal()
