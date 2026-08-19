"""SQLAlchemy ORM models."""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    links: Mapped[list["Link"]] = relationship(back_populates="owner", cascade="all, delete-orphan")
    api_keys: Mapped[list["ApiKey"]] = relationship(back_populates="owner", cascade="all, delete-orphan")


class ApiKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    # We store only a hash of the key; the plaintext is shown once at creation.
    key_prefix: Mapped[str] = mapped_column(String(12), index=True)
    hashed_key: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    # Per-key monthly usage quota (0 = unlimited).
    monthly_quota: Mapped[int] = mapped_column(Integer, default=10000)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    owner: Mapped["User"] = relationship(back_populates="api_keys")


class Link(Base):
    __tablename__ = "links"

    id: Mapped[int] = mapped_column(primary_key=True)
    short_code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    original_url: Mapped[str] = mapped_column(String(2048))
    owner_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    # Denormalized counter for fast dashboard reads; the source of truth is ClickEvent.
    click_count: Mapped[int] = mapped_column(BigInteger, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    owner: Mapped[Optional["User"]] = relationship(back_populates="links")
    clicks: Mapped[list["ClickEvent"]] = relationship(
        back_populates="link", cascade="all, delete-orphan"
    )


class ClickEvent(Base):
    __tablename__ = "click_events"

    # BigInteger for scale on PostgreSQL; falls back to autoincrementing INTEGER
    # on SQLite (used in tests), which doesn't autoincrement BIGINT PKs.
    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), primary_key=True
    )
    link_id: Mapped[int] = mapped_column(ForeignKey("links.id", ondelete="CASCADE"), index=True)
    clicked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)

    ip_address: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    device_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)  # mobile/tablet/pc/bot
    browser: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    os: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    referrer: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    link: Mapped["Link"] = relationship(back_populates="clicks")


# Composite index to speed up per-link time-series analytics queries.
Index("ix_click_events_link_time", ClickEvent.link_id, ClickEvent.clicked_at)
