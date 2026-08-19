"""Pydantic request/response models."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl


# ---- Auth ----
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserOut(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---- Links ----
class LinkCreate(BaseModel):
    original_url: HttpUrl
    custom_alias: Optional[str] = Field(
        default=None, min_length=3, max_length=32, pattern=r"^[a-zA-Z0-9_-]+$"
    )
    expires_at: Optional[datetime] = None


class LinkOut(BaseModel):
    id: int
    short_code: str
    short_url: str
    original_url: str
    click_count: int
    is_active: bool
    expires_at: Optional[datetime]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---- API keys ----
class ApiKeyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    monthly_quota: int = Field(default=10000, ge=0)


class ApiKeyOut(BaseModel):
    id: int
    name: str
    key_prefix: str
    is_active: bool
    monthly_quota: int
    created_at: datetime
    last_used_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class ApiKeyCreated(ApiKeyOut):
    # Full plaintext key, returned only once at creation time.
    api_key: str


# ---- Analytics ----
class TimeseriesPoint(BaseModel):
    date: str
    clicks: int


class BreakdownItem(BaseModel):
    label: str
    clicks: int


class LinkAnalytics(BaseModel):
    short_code: str
    total_clicks: int
    unique_visitors: int
    timeseries: list[TimeseriesPoint]
    by_country: list[BreakdownItem]
    by_device: list[BreakdownItem]
    by_browser: list[BreakdownItem]
    by_referrer: list[BreakdownItem]
