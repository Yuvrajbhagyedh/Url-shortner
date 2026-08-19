"""SQLAlchemy engine, session factory, and declarative base."""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import settings

# Managed Postgres providers (e.g. Render, Heroku) hand out a legacy
# "postgres://" URL, which SQLAlchemy 2.x no longer recognizes. Normalize it to
# the psycopg2 dialect form so those URLs work unchanged.
_db_url = settings.database_url
if _db_url.startswith("postgres://"):
    _db_url = "postgresql+psycopg2://" + _db_url[len("postgres://") :]

# SQLite (used in tests) doesn't accept the QueuePool sizing kwargs, so only
# pass them for real server databases like PostgreSQL.
_engine_kwargs: dict = {"pool_pre_ping": True}
if not _db_url.startswith("sqlite"):
    _engine_kwargs.update(pool_size=10, max_overflow=20)

engine = create_engine(_db_url, **_engine_kwargs)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
