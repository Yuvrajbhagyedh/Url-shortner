"""Celery tasks.

The redirect endpoint stays fast by doing zero analytics work inline: it only
enqueues `record_click`. The worker then enriches the raw request data (geo,
device, browser) and writes the ClickEvent row plus the denormalized counter.
This is the core system-design idea — decouple the hot redirect path from the
slower analytics write path.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import update

from .celery_app import celery_app
from .database import SessionLocal
from .models import ClickEvent, Link
from .services.enrichment import lookup_geo, parse_user_agent


@celery_app.task(name="app.tasks.record_click", bind=True, max_retries=3, default_retry_delay=5)
def record_click(
    self,
    link_id: int,
    ip_address: Optional[str],
    user_agent: Optional[str],
    referrer: Optional[str],
    clicked_at_iso: str,
):
    db = SessionLocal()
    try:
        ua = parse_user_agent(user_agent)
        geo = lookup_geo(ip_address)

        event = ClickEvent(
            link_id=link_id,
            clicked_at=datetime.fromisoformat(clicked_at_iso),
            ip_address=ip_address,
            country=geo["country"],
            city=geo["city"],
            device_type=ua["device_type"],
            browser=ua["browser"],
            os=ua["os"],
            referrer=referrer,
            user_agent=(user_agent or "")[:512],
        )
        db.add(event)
        db.execute(
            update(Link).where(Link.id == link_id).values(click_count=Link.click_count + 1)
        )
        db.commit()
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        raise self.retry(exc=exc)
    finally:
        db.close()
