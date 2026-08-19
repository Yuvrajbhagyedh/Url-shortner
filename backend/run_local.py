"""One-command local runner for ShortX (no Docker / Postgres / Redis needed).

Sets the zero-service environment BEFORE the app imports, then serves the API:
  - SQLite instead of PostgreSQL (tables auto-create on startup)
  - in-process fakeredis instead of Redis
  - Celery tasks run inline (eager) instead of via a worker

Usage:  python run_local.py
API:    http://localhost:8000        Docs: http://localhost:8000/docs
"""
import os

os.environ.setdefault("SHORTX_LOCAL", "1")
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///./shortx.db")
os.environ.setdefault("JWT_SECRET", "local-dev-secret-change-me")

import uvicorn  # noqa: E402

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
