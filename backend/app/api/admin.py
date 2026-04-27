import os
import shutil
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlmodel import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.track import Track, Album, Artist
from app.schemas.auth import UserCreate, UserUpdate
from app.utils.deps import get_current_user
from app.services.library_scanner import LibraryScanner
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin"])


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to check if user is admin."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


@router.get("/status")
async def get_server_status(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get server status and statistics."""
    import psutil
    
    # Get CPU usage
    cpu_percent = psutil.cpu_percent(interval=1)
    
    # Get memory usage
    memory = psutil.virtual_memory()
    
    # Get disk usage
    disk = psutil.disk_usage(str(settings.music_dir))
    
    # Get track count
    count_statement = select(func.count(Track.id))
    result = await db.exec(count_statement)
    tracks_count = result.one()
    
    # Get album count
    count_statement = select(func.count(Album.id))
    result = await db.exec(count_statement)
    albums_count = result.one()
    
    # Get artist count
    count_statement = select(func.count(Artist.id))
    result = await db.exec(count_statement)
    artists_count = result.one()
    
    # Get user count
    count_statement = select(func.count(User.id))
    result = await db.exec(count_statement)
    users_count = result.one()
    
    return {
        "cpu_percent": cpu_percent,
        "memory_total": memory.total,
        "memory_used": memory.used,
        "memory_percent": memory.percent,
        "disk_total": disk.total,
        "disk_used": disk.used,
        "disk_free": disk.free,
        "disk_percent": disk.percent,
        "tracks_count": tracks_count,
        "albums_count": albums_count,
        "artists_count": artists_count,
        "users_count": users_count,
        "active_sessions": 1,  # Could be enhanced with Redis session tracking
        "music_dir": str(settings.music_dir),
        "cache_dir": str(settings.cache_dir),
    }


@router.post("/scan")
async def start_library_scan(
    path: str = Form(default="/data/music"),
    force_rescan: bool = Form(default=False),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Start library scan process."""
    logger.info(f"Starting library scan: path={path}, force_rescan={force_rescan}")
    
    music_path = Path(path)
    if not music_path.exists():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Path does not exist: {path}"
        )
    
    try:
        scanner = LibraryScanner(music_dir=path, db=db)
        stats = await scanner.scan(force_rescan=force_rescan)
        
        # Commit changes
        await db.commit()
        
        logger.info(f"Library scan completed: {stats}")
        
        return {
            "task_id": "scan_" + datetime.utcnow().isoformat(),
            "status": "completed",
            "stats": stats,
        }
    except Exception as e:
        logger.exception(f"Scan failed: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scan failed: {str(e)}"
        )


@router.get("/users")
async def get_users(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> List[User]:
    """Get all users."""
    statement = select(User).order_by(User.created_at)
    result = await db.exec(statement)
    return result.all()


@router.post("/users")
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Create a new user."""
    # Check if username already exists
    statement = select(User).where(User.username == user_data.username)
    result = await db.exec(statement)
    if result.first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    statement = select(User).where(User.email == user_data.email)
    result = await db.exec(statement)
    if result.first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    from app.utils.security import get_password_hash
    
    user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        is_admin=user_data.is_admin,
        is_active=True,
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    logger.info(f"Created user: {user.username}")
    
    return user


@router.put("/users/{user_id}")
async def update_user(
    user_id: str,
    updates: UserUpdate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Update user details."""
    statement = select(User).where(User.id == user_id)
    result = await db.exec(statement)
    user = result.first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent removing own admin status
    if user.id == current_user.id and updates.is_admin is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove your own admin privileges"
        )
    
    # Update fields
    if updates.is_admin is not None:
        user.is_admin = updates.is_admin
    if updates.is_active is not None:
        user.is_active = updates.is_active
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    logger.info(f"Updated user: {user.username}")
    
    return user


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Delete a user."""
    statement = select(User).where(User.id == user_id)
    result = await db.exec(statement)
    user = result.first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent deleting yourself
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself"
        )
    
    await db.delete(user)
    await db.commit()
    
    logger.info(f"Deleted user: {user.username}")
    
    return {"message": "User deleted successfully"}


@router.post("/upload")
async def upload_music_file(
    file: UploadFile = File(...),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Upload a music file to the server."""
    # Validate file type
    allowed_extensions = {".mp3", ".flac", ".wav", ".m4a", ".ogg", ".aac"}
    file_ext = Path(file.filename or "").suffix.lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Create upload directory if it doesn't exist
    upload_dir = settings.music_dir / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Save file
    file_path = upload_dir / (file.filename or "unknown")
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"Uploaded file: {file_path}")
        
        # Optionally trigger a scan of the uploaded file
        # For now, just return success - user can trigger scan manually
        
        return {
            "message": "File uploaded successfully",
            "file_path": str(file_path),
            "filename": file.filename,
            "size": file.size,
        }
    except Exception as e:
        logger.exception(f"Upload failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )
