from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# User schemas
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    cache_limit_mb: Optional[int] = None


class UserResponse(UserBase):
    id: str
    is_admin: bool
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    cache_limit_mb: int

    class Config:
        from_attributes = True


# Auth schemas
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    user_id: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str
    device_name: Optional[str] = None


class RegisterRequest(UserCreate):
    pass


class RefreshTokenRequest(BaseModel):
    refresh_token: str
