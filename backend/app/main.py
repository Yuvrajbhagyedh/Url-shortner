"""ShortX FastAPI application entrypoint."""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .database import Base, engine
from .redis_client import redis_client
from .routers import analytics, apikeys, auth, links, public_api, redirect


def frontend_dir() -> Path:
    if settings.frontend_dist:
        return Path(settings.frontend_dist)
    return Path(__file__).resolve().parents[2] / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # For a demo/dev deployment we create tables on startup. In production this
    # is handled by Alembic migrations (see backend/alembic).
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="ShortX API",
    version="1.0.0",
    description="URL shortener with click analytics, API keys, and rate limiting.",
    lifespan=lifespan,
)

_cors = settings.cors_origin_list
_allow_all = _cors == ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if _allow_all else _cors,
    allow_credentials=not _allow_all,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["meta"])
def health():
    try:
        redis_ok = redis_client.ping()
    except Exception:
        redis_ok = False
    return {"status": "ok", "service": settings.app_name, "redis": redis_ok}


# API routers (order matters: the catch-all redirect route is registered last).
app.include_router(auth.router)
app.include_router(links.router)
app.include_router(apikeys.router)
app.include_router(analytics.router)
app.include_router(public_api.router)

_dist = frontend_dir()
_assets = _dist / "assets"
if _assets.is_dir():
    app.mount("/assets", StaticFiles(directory=str(_assets)), name="frontend-assets")

_SPA_PREFIXES = ("login", "keys", "analytics")


def _spa_index():
    index = frontend_dir() / "index.html"
    if not index.is_file():
        raise HTTPException(status_code=500, detail="Frontend build is missing")
    return FileResponse(index)


@app.api_route("/", methods=["GET", "HEAD"])
def spa_root():
    if (frontend_dir() / "index.html").is_file():
        return _spa_index()
    raise HTTPException(status_code=404, detail="Not found")


@app.api_route("/login", methods=["GET", "HEAD"])
@app.api_route("/keys", methods=["GET", "HEAD"])
def spa_pages():
    return _spa_index()


@app.api_route("/analytics/{code}", methods=["GET", "HEAD"])
def spa_analytics(code: str):
    return _spa_index()


app.include_router(redirect.router)  # GET /{short_code} — must be last
