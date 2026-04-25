"""Tracks API endpoints with search, filtering, and pagination."""

from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_

from app.database import get_db
from app.schemas.track import (
    TrackResponse,
    TrackListResponse,
    AlbumResponse,
    ArtistResponse,
)
from app.models.track import Track, Album, Artist
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/tracks", tags=["Tracks"])


@router.get("", response_model=TrackListResponse)
async def list_tracks(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    q: Optional[str] = Query(None, description="Search query"),
    artist_id: Optional[str] = Query(None, description="Filter by artist"),
    album_id: Optional[str] = Query(None, description="Filter by album"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
):
    """List tracks with optional search, filtering, and pagination."""
    # Build base query
    query = select(Track)
    
    # Apply filters
    filters = []
    if artist_id:
        filters.append(Track.artist_id == artist_id)
    if album_id:
        filters.append(Track.album_id == album_id)
    if q:
        # Simple search by title
        filters.append(Track.title.ilike(f"%{q}%"))
    
    if filters:
        query = query.where(and_(*filters))
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    # Execute query
    result = await db.execute(query)
    tracks = result.scalars().all()
    
    # Calculate pages
    pages = (total + page_size - 1) // page_size
    
    return TrackListResponse(
        items=[TrackResponse.model_validate(t) for t in tracks],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/{track_id}", response_model=TrackResponse)
async def get_track(
    track_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get a specific track by ID."""
    result = await db.execute(select(Track).where(Track.id == track_id))
    track = result.scalar_one_or_none()
    
    if not track:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Track not found"
        )
    
    return track


@router.get("/{track_id}/album", response_model=AlbumResponse)
async def get_track_album(
    track_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get the album for a specific track."""
    track_result = await db.execute(select(Track).where(Track.id == track_id))
    track = track_result.scalar_one_or_none()
    
    if not track:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Track not found"
        )
    
    if not track.album_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Track has no album"
        )
    
    album_result = await db.execute(select(Album).where(Album.id == track.album_id))
    album = album_result.scalar_one_or_none()
    
    if not album:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Album not found"
        )
    
    return album


@router.get("/{track_id}/artist", response_model=ArtistResponse)
async def get_track_artist(
    track_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get the artist for a specific track."""
    track_result = await db.execute(select(Track).where(Track.id == track_id))
    track = track_result.scalar_one_or_none()
    
    if not track:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Track not found"
        )
    
    if not track.artist_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Track has no artist"
        )
    
    artist_result = await db.execute(select(Artist).where(Artist.id == track.artist_id))
    artist = artist_result.scalar_one_or_none()
    
    if not artist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artist not found"
        )
    
    return artist
