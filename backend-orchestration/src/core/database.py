"""
SQLAlchemy engine, session factory, declarative Base, and the `get_db`
FastAPI dependency used by every route that touches the database.

Synchronous SQLAlchemy is used deliberately (not async/asyncpg) to keep
this service's dependency footprint small and its behavior easy to reason
about; the traffic this backend serves (job creation, dashboard reads) is
low-volume enough that this isn't a bottleneck.
"""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from src.core.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
