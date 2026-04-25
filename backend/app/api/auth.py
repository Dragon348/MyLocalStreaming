from fastapi import APIRouter, HTTPException, Depends, status
from app.schemas.auth import UserCreate, UserLogin, Token, UserResponse

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """Register a new user."""
    # TODO: Implement registration logic
    pass


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin):
    """Login and get access/refresh tokens."""
    # TODO: Implement login logic
    pass
