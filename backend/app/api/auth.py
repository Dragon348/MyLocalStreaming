from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.session import Session
from app.schemas.auth import (
    UserCreate,
    UserResponse,
    Token,
    LoginRequest,
    RegisterRequest,
    RefreshTokenRequest,
)
from app.utils.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    hash_refresh_token,
    verify_refresh_token,
)
from app.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> User:
    """Register a new user."""
    # Check if username exists
    statement = select(User).where(User.username == user_data.username)
    result = await db.exec(statement)
    if result.first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    # Check if email exists
    statement = select(User).where(User.email == user_data.email)
    result = await db.exec(statement)
    if result.first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create user
    hashed_password = get_password_hash(user_data.password)
    user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user


@router.post("/login", response_model=Token)
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Login and get access/refresh tokens."""
    # Find user by username
    statement = select(User).where(User.username == login_data.username)
    result = await db.exec(statement)
    user = result.first()

    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    # Update last login
    user.last_login = datetime.utcnow()
    await db.commit()

    # Create tokens
    access_token = create_access_token(
        data={"sub": user.id},
        secret_key=settings.jwt_secret,
    )
    refresh_token = create_refresh_token()

    # Store session
    session = Session(
        user_id=user.id,
        refresh_token_hash=hash_refresh_token(refresh_token),
        device_name=login_data.device_name,
        expires_at=Session.get_expiry(),
    )
    db.add(session)
    await db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": 60 * 60,  # 1 hour in seconds
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(
    token_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Refresh access token using refresh token."""
    # Find session by refresh token
    statement = select(Session).where(Session.refresh_token_hash == hash_refresh_token(token_data.refresh_token))
    result = await db.exec(statement)
    session = result.first()

    if not session or session.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify the refresh token matches
    if not verify_refresh_token(token_data.refresh_token, session.refresh_token_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user
    statement = select(User).where(User.id == session.user_id)
    result = await db.exec(statement)
    user = result.first()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create new access token
    access_token = create_access_token(
        data={"sub": user.id},
        secret_key=settings.jwt_secret,
    )

    return {
        "access_token": access_token,
        "refresh_token": token_data.refresh_token,
        "token_type": "bearer",
        "expires_in": 60 * 60,
    }


@router.post("/logout")
async def logout(
    token_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Logout and invalidate the session."""
    # Find and delete session
    statement = select(Session).where(Session.refresh_token_hash == hash_refresh_token(token_data.refresh_token))
    result = await db.exec(statement)
    session = result.first()

    if session:
        db.delete(session)
        await db.commit()

    return {"message": "Successfully logged out"}
