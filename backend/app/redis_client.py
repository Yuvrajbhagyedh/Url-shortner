"""Shared Redis connection used for caching and rate limiting."""
import os

import redis

from .config import settings


def _use_fake() -> bool:
    flag = os.getenv("SHORTX_LOCAL", "").lower() in {"1", "true", "yes"}
    return flag or settings.redis_url.startswith("memory")


def _make_client():
    """Return a Redis client.

    In a normal deployment this is a real Redis connection. For a zero-service
    local/demo run (SHORTX_LOCAL=1 or REDIS_URL=memory://) or when Redis is
    unreachable, fall back to an in-process fakeredis.
    """
    if _use_fake():
        import fakeredis

        return fakeredis.FakeStrictRedis(decode_responses=True)

    client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
    try:
        client.ping()
        return client
    except Exception:
        try:
            import fakeredis

            return fakeredis.FakeStrictRedis(decode_responses=True)
        except Exception:
            return client


# decode_responses=True so we work with str instead of bytes.
redis_client = _make_client()


def cache_key(short_code: str) -> str:
    return f"shortx:url:{short_code}"
