import re
from pathlib import Path
from typing import Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.track import Track, Album, Artist
from app.schemas.track import (
    TrackResponse,
    TrackListResponse,
    TrackSearchRequest,
)
from app.utils.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/tracks", tags=["Tracks"])


@router.get("", response_model=TrackListResponse)
async def list_tracks(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    artist_id: Optional[str] = None,
    album_id: Optional[str] = None,
    sort: str = "title",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List tracks with pagination and filtering."""
    # Build query
    statement = select(Track)

    # Apply filters
    if artist_id:
        statement = statement.where(Track.artist_id == artist_id)
    if album_id:
        statement = statement.where(Track.album_id == album_id)

    # Apply sorting
    valid_sort_fields = {"title", "created_at", "duration_ms", "play_count"}
    if sort not in valid_sort_fields:
        sort = "title"
    statement = statement.order_by(getattr(Track, sort))

    # Get total count
    count_statement = select(func.count(Track.id))
    if artist_id:
        count_statement = count_statement.where(Track.artist_id == artist_id)
    if album_id:
        count_statement = count_statement.where(Track.album_id == album_id)
    total_result = await db.exec(count_statement)
    total = total_result.one()

    # Apply pagination
    statement = statement.offset(offset).limit(limit)
    result = await db.exec(statement)
    tracks = result.all()

    return {
        "items": tracks,
        "total": total,
        "offset": offset,
        "limit": limit,
    }


@router.get("/{track_id}", response_model=TrackResponse)
async def get_track(
    track_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Track:
    """Get a specific track by ID."""
    statement = select(Track).where(Track.id == track_id)
    result = await db.exec(statement)
    track = result.first()

    if not track:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Track not found")

    return track


@router.get("/random", response_model=list[TrackResponse])
async def get_random_tracks(
    limit: int = Query(default=10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Track]:
    """Get random tracks for shuffle mode."""
    # Use database-specific random function
    statement = select(Track).order_by(func.random()).limit(limit)
    result = await db.exec(statement)
    return result.all()


@router.put("/{track_id}/play")
async def increment_play_count(
    track_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Increment play count for a track."""
    from datetime import datetime

    statement = select(Track).where(Track.id == track_id)
    result = await db.exec(statement)
    track = result.first()

    if not track:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Track not found")

    track.play_count += 1
    track.last_played = datetime.utcnow()
    await db.commit()
    await db.refresh(track)

    return {"message": "Play count incremented", "play_count": track.play_count}


@router.get("/search", response_model=TrackListResponse)
async def search_tracks(
    q: Optional[str] = Query(None, min_length=1),
    artist_id: Optional[str] = None,
    album_id: Optional[str] = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Search tracks by title, artist, or album."""
    statement = select(Track)

    if q:
        # Simple case-insensitive search
        search_pattern = f"%{q.lower()}%"
        statement = statement.where(
            (Track.title.ilike(search_pattern))
        )

    if artist_id:
        statement = statement.where(Track.artist_id == artist_id)
    if album_id:
        statement = statement.where(Track.album_id == album_id)

    # Get total count
    count_statement = select(func.count(Track.id)).select_from(statement.subquery())
    total_result = await db.exec(count_statement)
    total = total_result.one()

    # Apply pagination
    statement = statement.order_by(Track.title).offset(offset).limit(limit)
    result = await db.exec(statement)
    tracks = result.all()

    return {
        "items": tracks,
        "total": total,
        "offset": offset,
        "limit": limit,
    }
