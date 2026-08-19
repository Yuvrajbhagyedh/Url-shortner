"""Analytics: time-series and dimensional breakdowns per link."""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_user
from ..models import ClickEvent, Link, User
from ..schemas import BreakdownItem, LinkAnalytics, TimeseriesPoint

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


def _owned_link(short_code: str, db: Session, user: User) -> Link:
    link = db.query(Link).filter(Link.short_code == short_code).first()
    if not link or link.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")
    return link


def _breakdown(db: Session, link_id: int, column) -> list[BreakdownItem]:
    rows = (
        db.query(column, func.count(ClickEvent.id))
        .filter(ClickEvent.link_id == link_id)
        .group_by(column)
        .order_by(func.count(ClickEvent.id).desc())
        .limit(10)
        .all()
    )
    return [BreakdownItem(label=label or "unknown", clicks=count) for label, count in rows]


@router.get("/{short_code}", response_model=LinkAnalytics)
def link_analytics(
    short_code: str,
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    link = _owned_link(short_code, db, current_user)
    since = datetime.now(timezone.utc) - timedelta(days=days)

    total = db.query(func.count(ClickEvent.id)).filter(ClickEvent.link_id == link.id).scalar() or 0
    unique = (
        db.query(func.count(func.distinct(ClickEvent.ip_address)))
        .filter(ClickEvent.link_id == link.id)
        .scalar()
        or 0
    )

    # Daily time-series (DB-agnostic: bucket in Python from raw timestamps).
    raw = (
        db.query(ClickEvent.clicked_at)
        .filter(ClickEvent.link_id == link.id, ClickEvent.clicked_at >= since)
        .all()
    )
    buckets: dict[str, int] = {}
    for (ts,) in raw:
        day = ts.astimezone(timezone.utc).strftime("%Y-%m-%d")
        buckets[day] = buckets.get(day, 0) + 1

    timeseries = []
    for i in range(days):
        day = (since + timedelta(days=i + 1)).strftime("%Y-%m-%d")
        timeseries.append(TimeseriesPoint(date=day, clicks=buckets.get(day, 0)))

    return LinkAnalytics(
        short_code=link.short_code,
        total_clicks=total,
        unique_visitors=unique,
        timeseries=timeseries,
        by_country=_breakdown(db, link.id, ClickEvent.country),
        by_device=_breakdown(db, link.id, ClickEvent.device_type),
        by_browser=_breakdown(db, link.id, ClickEvent.browser),
        by_referrer=_breakdown(db, link.id, ClickEvent.referrer),
    )
