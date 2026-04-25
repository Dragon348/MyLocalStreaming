"""Authentication schemas for request/response validation."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """Schema for user registration."""

    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class UserLogin(BaseModel):
    """Schema for user login."""

    username: str
    password: str


class Token(BaseModel):
    """Schema for JWT token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for decoded token data."""

    user_id: Optional[str] = None
    username: Optional[str] = None
    exp: Optional[datetime] = None
    type: Optional[str] = None


class UserResponse(BaseModel):
    """Schema for user response (without sensitive data)."""

    id: str
    username: str
    email: str
    is_admin: bool
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    cache_limit_mb: int = 1024

    class Config:
        from_attributes = True
