"""ShortX FastAPI application entrypoint."""
from contextlib import asynccontextmanager
from mimetypes import guess_type
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from .config import settings
from .database import Base, engine
from .redis_client import redis_client
from .routers import analytics, apikeys, auth, links, public_api, redirect


def frontend_dir() -> Path:
    candidates = []
    if settings.frontend_dist:
        candidates.append(Path(settings.frontend_dist))
    here = Path(__file__).resolve()
    candidates.extend(
        [
            here.parents[1] / "frontend" / "dist",  # /app/frontend/dist in Docker
            here.parents[2] / "frontend" / "dist",  # repo layout
            Path("/app/frontend/dist"),
            Path("/frontend/dist"),
        ]
    )
    for path in candidates:
        if (path / "index.html").is_file():
            return path
    return candidates[0]


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
    dist = frontend_dir()
    try:
        redis_ok = redis_client.ping()
    except Exception:
        redis_ok = False
    return {
        "status": "ok",
        "service": settings.app_name,
        "redis": redis_ok,
        "frontend": (dist / "index.html").is_file(),
        "frontend_dist": str(dist),
    }


# API routers (order matters: the catch-all redirect route is registered last).
app.include_router(auth.router)
app.include_router(links.router)
app.include_router(apikeys.router)
app.include_router(analytics.router)
app.include_router(public_api.router)


def _spa_index():
    index = frontend_dir() / "index.html"
    if not index.is_file():
        raise HTTPException(status_code=500, detail="Frontend build is missing")
    return FileResponse(index, media_type="text/html")


@app.api_route("/assets/{asset_path:path}", methods=["GET", "HEAD"])
def spa_assets(asset_path: str):
    """Serve Vite assets with correct MIME types (avoids text/plain 404s)."""
    base = (frontend_dir() / "assets").resolve()
    target = (base / asset_path).resolve()
    if not str(target).startswith(str(base)) or not target.is_file():
        raise HTTPException(status_code=404, detail="Asset not found")
    media_type, _ = guess_type(str(target))
    if target.suffix == ".css":
        media_type = "text/css"
    elif target.suffix == ".js":
        media_type = "application/javascript"
    return FileResponse(target, media_type=media_type or "application/octet-stream")


@app.api_route("/", methods=["GET", "HEAD"])
def spa_root():
    if (frontend_dir() / "index.html").is_file():
        return _spa_index()
    raise HTTPException(status_code=404, detail="Frontend build is missing")


@app.api_route("/login", methods=["GET", "HEAD"])
@app.api_route("/keys", methods=["GET", "HEAD"])
def spa_pages():
    return _spa_index()


@app.api_route("/analytics/{code}", methods=["GET", "HEAD"])
def spa_analytics(code: str):
    return _spa_index()


app.include_router(redirect.router)  # GET /{short_code} — must be last
