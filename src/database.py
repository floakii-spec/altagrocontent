# src/database.py
from functools import lru_cache
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session


@lru_cache(maxsize=1)
def _get_engine():
    from src.config import DATABASE_URL
    return create_engine(DATABASE_URL, pool_pre_ping=True)


def get_session() -> Session:
    SessionLocal = sessionmaker(bind=_get_engine())
    return SessionLocal()
