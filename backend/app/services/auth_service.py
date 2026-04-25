"""Authentication service for user management and JWT tokens."""

from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.models.session import Session
from app.schemas.auth import UserCreate, Token
from app.utils.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
)


class AuthService:
    """Service for authentication operations."""

    def __init__(self, db: AsyncSession, secret_key: str):
        self.db = db
        self.secret_key = secret_key

    async def register(self, user_data: UserCreate) -> User:
        """Register a new user."""
        hashed_password = get_password_hash(user_data.password)
        
        user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
        )
        
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        
        return user

    async def authenticate(self, username: str, password: str) -> Optional[User]:
        """Authenticate a user by username and password."""
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        user = result.scalar_one_or_none()
        
        if not user or not verify_password(password, user.hashed_password):
            return None
        
        # Update last login
        user.last_login = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(user)
        
        return user

    async def create_session(
        self,
        user: User,
        device_name: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> tuple[str, str]:
        """Create a session with access and refresh tokens."""
        refresh_token = create_refresh_token()
        
        access_token = create_access_token(
            data={"user_id": user.id, "username": user.username},
            secret_key=self.secret_key,
        )
        
        session = Session(
            user_id=user.id,
            refresh_token_hash=get_password_hash(refresh_token),
            device_name=device_name,
            ip_address=ip_address,
            expires_at=Session.get_expiry(),
        )
        
        self.db.add(session)
        await self.db.commit()
        
        return access_token, refresh_token

    async def refresh_tokens(self, refresh_token: str) -> Optional[tuple[str, str]]:
        """Refresh access and refresh tokens."""
        # Find session by refresh token
        result = await self.db.execute(
            select(Session).where(Session.refresh_token_hash.like(f"%{refresh_token[-10:]}%"))
        )
        sessions = result.scalars().all()
        
        valid_session = None
        for session in sessions:
            if verify_password(refresh_token, session.refresh_token_hash):
                if session.expires_at > datetime.utcnow():
                    valid_session = session
                    break
        
        if not valid_session:
            return None
        
        # Get user
        user_result = await self.db.execute(
            select(User).where(User.id == valid_session.user_id)
        )
        user = user_result.scalar_one_or_none()
        
        if not user or not user.is_active:
            return None
        
        # Create new tokens
        new_refresh_token = create_refresh_token()
        new_access_token = create_access_token(
            data={"user_id": user.id, "username": user.username},
            secret_key=self.secret_key,
        )
        
        # Update session
        valid_session.refresh_token_hash = get_password_hash(new_refresh_token)
        valid_session.expires_at = Session.get_expiry()
        await self.db.commit()
        
        return new_access_token, new_refresh_token

    async def revoke_session(self, refresh_token: str) -> bool:
        """Revoke a session by refresh token."""
        result = await self.db.execute(
            select(Session).where(Session.refresh_token_hash.like(f"%{refresh_token[-10:]}%"))
        )
        sessions = result.scalars().all()
        
        for session in sessions:
            if verify_password(refresh_token, session.refresh_token_hash):
                await self.db.delete(session)
                await self.db.commit()
                return True
        
        return False

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
