from datetime import datetime, timedelta
from typing import Optional
from sqlmodel import Field, SQLModel
import uuid


class Session(SQLModel, table=True):
    __tablename__ = "sessions"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    refresh_token_hash: str = Field(index=True)
    device_name: Optional[str] = None
    ip_address: Optional[str] = None
    expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @classmethod
    def get_expiry(cls, days: int = 30) -> datetime:
        return datetime.utcnow() + timedelta(days=days)
