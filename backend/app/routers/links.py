"""Link management: create, list, delete, and QR code generation."""
import io
from typing import Optional

import qrcode
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..dependencies import api_rate_limit, get_current_user
from ..models import Link, User
from ..redis_client import cache_key, redis_client
from ..schemas import LinkCreate, LinkOut
from ..services.shortcode import generate_short_code

router = APIRouter(prefix="/api/links", tags=["links"])


def _to_out(link: Link) -> LinkOut:
    return LinkOut(
        id=link.id,
        short_code=link.short_code,
        short_url=f"{settings.base_url}/{link.short_code}",
        original_url=link.original_url,
        click_count=link.click_count,
        is_active=link.is_active,
        expires_at=link.expires_at,
        created_at=link.created_at,
    )


def _create_link(payload: LinkCreate, db: Session, owner_id: Optional[int]) -> Link:
    if payload.custom_alias:
        if db.query(Link).filter(Link.short_code == payload.custom_alias).first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Alias already taken"
            )
        short_code = payload.custom_alias
    else:
        # Retry on the (rare) chance of a random collision.
        for _ in range(5):
            candidate = generate_short_code(settings.short_code_length)
            if not db.query(Link).filter(Link.short_code == candidate).first():
                short_code = candidate
                break
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not allocate a short code",
            )

    link = Link(
        short_code=short_code,
        original_url=str(payload.original_url),
        owner_id=owner_id,
        expires_at=payload.expires_at,
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    return link


@router.post("", response_model=LinkOut, status_code=status.HTTP_201_CREATED)
def create_link(
    payload: LinkCreate,
    _: None = Depends(api_rate_limit),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    link = _create_link(payload, db, owner_id=current_user.id)
    return _to_out(link)


@router.get("", response_model=list[LinkOut])
def list_links(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    links = (
        db.query(Link)
        .filter(Link.owner_id == current_user.id)
        .order_by(Link.created_at.desc())
        .all()
    )
    return [_to_out(link) for link in links]


@router.delete("/{short_code}", status_code=status.HTTP_204_NO_CONTENT)
def delete_link(
    short_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    link = db.query(Link).filter(Link.short_code == short_code).first()
    if not link or link.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")
    db.delete(link)
    db.commit()
    # Invalidate any cached redirect entry.
    redis_client.delete(cache_key(short_code))


@router.get("/{short_code}/qr")
def link_qr(
    short_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    link = db.query(Link).filter(Link.short_code == short_code).first()
    if not link or link.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")

    img = qrcode.make(f"{settings.base_url}/{link.short_code}")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")
