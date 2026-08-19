"""ShortX FastAPI application entrypoint."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import Base, engine
from .redis_client import redis_client
from .routers import analytics, apikeys, auth, links, public_api, redirect


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

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
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
app.include_router(redirect.router)  # GET /{short_code} — must be last
