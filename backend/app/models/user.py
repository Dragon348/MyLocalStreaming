from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel
import uuid
from pydantic import EmailStr, field_validator


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    username: str = Field(unique=True, index=True, min_length=3, max_length=50)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    is_admin: bool = Field(default=False)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None

    # Cache limit on device (in MB)
    cache_limit_mb: int = Field(default=1024)
