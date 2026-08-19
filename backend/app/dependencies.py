"""Shared FastAPI dependencies: authentication and rate limiting."""
from datetime import datetime, timezone
from typing import Optional

from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db
from .models import ApiKey, User
from .redis_client import redis_client
from .security import decode_access_token, hash_api_key

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Resolve the authenticated user from a JWT bearer token (dashboard)."""
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exc
    subject = decode_access_token(token)
    if subject is None:
        raise credentials_exc
    user = db.get(User, int(subject))
    if user is None or not user.is_active:
        raise credentials_exc
    return user


def get_api_key_owner(
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
    db: Session = Depends(get_db),
) -> tuple[User, ApiKey]:
    """Authenticate a programmatic request via an X-API-Key header."""
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing X-API-Key header"
        )
    prefix = x_api_key[:12]
    candidates = db.query(ApiKey).filter(ApiKey.key_prefix == prefix, ApiKey.is_active.is_(True)).all()
    hashed = hash_api_key(x_api_key)
    api_key = next((k for k in candidates if k.hashed_key == hashed), None)
    if api_key is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")

    # Enforce monthly quota (0 == unlimited) using a Redis counter.
    if api_key.monthly_quota > 0:
        month = datetime.now(timezone.utc).strftime("%Y%m")
        usage_key = f"shortx:apikey:{api_key.id}:usage:{month}"
        used = redis_client.incr(usage_key)
        if used == 1:
            redis_client.expire(usage_key, 60 * 60 * 24 * 31)
        if used > api_key.monthly_quota:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Monthly API quota exceeded",
            )

    api_key.last_used_at = datetime.now(timezone.utc)
    db.commit()
    owner = db.get(User, api_key.owner_id)
    return owner, api_key


def rate_limit(request: Request, limit_per_minute: int, bucket: str) -> None:
    """Fixed-window rate limiter backed by Redis.

    Keyed by client IP + bucket name. Raises 429 when the window budget is
    exhausted. If Redis is unavailable, fail open so the API stays usable.
    """
    client_ip = request.client.host if request.client else "unknown"
    window = datetime.now(timezone.utc).strftime("%Y%m%d%H%M")
    key = f"shortx:ratelimit:{bucket}:{client_ip}:{window}"
    try:
        current = redis_client.incr(key)
        if current == 1:
            redis_client.expire(key, 60)
    except Exception:
        return
    if current > limit_per_minute:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Try again shortly.",
            headers={"Retry-After": "60"},
        )


def api_rate_limit(request: Request) -> None:
    rate_limit(request, settings.rate_limit_per_minute, "api")
