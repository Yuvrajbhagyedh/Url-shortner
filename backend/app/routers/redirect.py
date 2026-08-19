"""The hot path: resolve a short code and 302-redirect the visitor.

Design goals for this endpoint:
  * O(1) lookup via a Redis cache in front of PostgreSQL.
  * Zero blocking analytics work — the click is handed to Celery and the
    response returns immediately.
  * Rate limited per IP to blunt abuse / scraping.
"""
import json
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..dependencies import rate_limit
from ..models import Link
from ..redis_client import cache_key, redis_client
from ..tasks import record_click

router = APIRouter(tags=["redirect"])


def _load_link(short_code: str, db: Session) -> Optional[dict]:
    """Return {id, url, expires_at} for an active link, using Redis as cache."""
    key = cache_key(short_code)
    cached = redis_client.get(key)
    if cached is not None:
        return json.loads(cached) if cached != "__MISS__" else None

    link = db.query(Link).filter(Link.short_code == short_code).first()
    if link is None or not link.is_active:
        # Negative-cache misses briefly to protect the DB from repeated bad codes.
        redis_client.set(key, "__MISS__", ex=60)
        return None

    data = {
        "id": link.id,
        "url": link.original_url,
        "expires_at": link.expires_at.isoformat() if link.expires_at else None,
    }
    redis_client.set(key, json.dumps(data), ex=settings.cache_ttl_seconds)
    return data


@router.get("/{short_code}")
def redirect(short_code: str, request: Request, db: Session = Depends(get_db)):
    rate_limit(request, settings.rate_limit_redirect_per_minute, "redirect")

    data = _load_link(short_code, db)
    if data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Short link not found")

    # Expiry check.
    if data["expires_at"]:
        expires = datetime.fromisoformat(data["expires_at"])
        if expires < datetime.now(timezone.utc):
            redis_client.delete(cache_key(short_code))
            raise HTTPException(status_code=status.HTTP_410_GONE, detail="Short link expired")

    # Hand analytics off to the worker — do not block the redirect.
    client_ip = request.client.host if request.client else None
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()

    try:
        record_click.delay(
            link_id=data["id"],
            ip_address=client_ip,
            user_agent=request.headers.get("user-agent"),
            referrer=request.headers.get("referer"),
            clicked_at_iso=datetime.now(timezone.utc).isoformat(),
        )
    except Exception:
        # Never break the redirect if analytics enqueue fails.
        pass

    return RedirectResponse(url=data["url"], status_code=status.HTTP_302_FOUND)
