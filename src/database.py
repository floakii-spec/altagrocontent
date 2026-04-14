# src/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session


def _make_engine():
    from src.config import DATABASE_URL
    return create_engine(DATABASE_URL, pool_pre_ping=True)


def get_session() -> Session:
    engine = _make_engine()
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()
