"""Pytest fixtures: an isolated SQLite DB, a fake Redis, and a stubbed worker.

These let the full API be exercised with a TestClient without needing
PostgreSQL, Redis, or a Celery worker actually running.
"""
import os

# Point the app at SQLite and dummy brokers BEFORE app modules import settings.
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("JWT_SECRET", "test-secret")

import fakeredis  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402


@pytest.fixture()
def client(monkeypatch):
    # Fresh in-memory SQLite shared across the connection pool.
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    from app import database, redis_client as rc
    from app.database import Base

    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    # Swap in a fake Redis everywhere the real client is referenced.
    fake = fakeredis.FakeStrictRedis(decode_responses=True)
    monkeypatch.setattr(rc, "redis_client", fake)
    monkeypatch.setattr("app.dependencies.redis_client", fake)
    monkeypatch.setattr("app.routers.links.redis_client", fake)
    monkeypatch.setattr("app.routers.redirect.redis_client", fake)

    # Make the analytics task a synchronous no-op in tests.
    monkeypatch.setattr("app.routers.redirect.record_click.delay", lambda **kw: None)

    from app.main import app

    app.dependency_overrides[database.get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def auth_client(client):
    """A client with a registered+logged-in user; returns (client, headers)."""
    client.post("/api/auth/register", json={"email": "a@b.com", "password": "password123"})
    resp = client.post(
        "/api/auth/login", data={"username": "a@b.com", "password": "password123"}
    )
    token = resp.json()["access_token"]
    return client, {"Authorization": f"Bearer {token}"}
