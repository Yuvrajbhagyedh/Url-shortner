"""Programmatic v1 API authenticated by X-API-Key (for external integrations)."""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..dependencies import api_rate_limit, get_api_key_owner
from ..models import ApiKey, User
from ..schemas import LinkCreate, LinkOut
from .links import _create_link, _to_out

router = APIRouter(prefix="/api/v1", tags=["public-api"])


@router.post("/shorten", response_model=LinkOut)
def shorten(
    payload: LinkCreate,
    request: Request,
    _: None = Depends(api_rate_limit),
    auth: tuple[User, ApiKey] = Depends(get_api_key_owner),
    db: Session = Depends(get_db),
):
    """Create a short link using an API key instead of a dashboard session."""
    owner, _api_key = auth
    link = _create_link(payload, db, owner_id=owner.id)
    return _to_out(link)
