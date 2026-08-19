"""Enrich raw click data into device / browser / geo attributes.

Device & browser parsing uses the `user_agents` library. Geo lookup is
pluggable: if a MaxMind GeoLite2 database is mounted at GEOIP_DB_PATH we use
it, otherwise geo fields are left as "Unknown". This keeps the project fully
runnable offline while allowing real geo-IP in production.
"""
from __future__ import annotations

import os

from user_agents import parse as parse_ua

_GEOIP_DB_PATH = os.getenv("GEOIP_DB_PATH", "")
_geo_reader = None

if _GEOIP_DB_PATH and os.path.exists(_GEOIP_DB_PATH):
    try:  # pragma: no cover - optional dependency
        import geoip2.database

        _geo_reader = geoip2.database.Reader(_GEOIP_DB_PATH)
    except Exception:
        _geo_reader = None


def parse_user_agent(ua_string: str | None) -> dict[str, str]:
    if not ua_string:
        return {"device_type": "unknown", "browser": "unknown", "os": "unknown"}

    ua = parse_ua(ua_string)
    if ua.is_bot:
        device_type = "bot"
    elif ua.is_mobile:
        device_type = "mobile"
    elif ua.is_tablet:
        device_type = "tablet"
    elif ua.is_pc:
        device_type = "desktop"
    else:
        device_type = "other"

    return {
        "device_type": device_type,
        "browser": ua.browser.family or "unknown",
        "os": ua.os.family or "unknown",
    }


def lookup_geo(ip_address: str | None) -> dict[str, str]:
    if not ip_address or _geo_reader is None:
        return {"country": "Unknown", "city": "Unknown"}
    try:  # pragma: no cover - optional dependency
        resp = _geo_reader.city(ip_address)
        return {
            "country": resp.country.name or "Unknown",
            "city": resp.city.name or "Unknown",
        }
    except Exception:
        return {"country": "Unknown", "city": "Unknown"}
