"""API key management for programmatic access."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_user
from ..models import ApiKey, User
from ..schemas import ApiKeyCreate, ApiKeyCreated, ApiKeyOut
from ..security import generate_api_key

router = APIRouter(prefix="/api/keys", tags=["api-keys"])


@router.post("", response_model=ApiKeyCreated, status_code=status.HTTP_201_CREATED)
def create_api_key(
    payload: ApiKeyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    full_key, prefix, hashed = generate_api_key()
    api_key = ApiKey(
        owner_id=current_user.id,
        name=payload.name,
        key_prefix=prefix,
        hashed_key=hashed,
        monthly_quota=payload.monthly_quota,
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)

    out = ApiKeyCreated(
        id=api_key.id,
        name=api_key.name,
        key_prefix=api_key.key_prefix,
        is_active=api_key.is_active,
        monthly_quota=api_key.monthly_quota,
        created_at=api_key.created_at,
        last_used_at=api_key.last_used_at,
        api_key=full_key,
    )
    return out


@router.get("", response_model=list[ApiKeyOut])
def list_api_keys(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(ApiKey)
        .filter(ApiKey.owner_id == current_user.id)
        .order_by(ApiKey.created_at.desc())
        .all()
    )


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_api_key(
    key_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    api_key = db.get(ApiKey, key_id)
    if not api_key or api_key.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
    db.delete(api_key)
    db.commit()
