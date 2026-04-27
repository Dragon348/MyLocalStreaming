import re
from pathlib import Path
from typing import Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Query, status, Header
from fastapi.responses import StreamingResponse
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
from app.services.streaming import (
    handle_stream_request,
    validate_bitrate,
    get_cache_stats,
    CURL_EXAMPLES,
)

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


@router.get("/stream/{track_id}")
async def stream_track(
    track_id: str,
    transcode: bool = Query(default=False, description="Transcode to Opus format"),
    bitrate: int = Query(default=128, ge=64, le=320, description="Bitrate in kbps for transcoding"),
    range_header: Optional[str] = Header(None, alias="Range"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Stream audio track with HTTP Range support and optional transcoding.
    
    Supports:
    - Full file streaming (200 OK)
    - Range requests for seeking (206 Partial Content)
    - On-the-fly transcoding to Opus (?transcode=true&bitrate=128)
    - LRU caching of transcoded files
    
    Args:
        track_id: Track UUID
        transcode: Enable transcoding to Opus
        bitrate: Target bitrate for transcoding (64-320 kbps)
        range_header: HTTP Range header for partial content
        
    Returns:
        StreamingResponse with audio data
        
    Examples:
        # Full stream
        GET /api/v1/stream/{track_id}
        
        # Range request (seek to 1MB)
        GET /api/v1/stream/{track_id}
        Header: Range: bytes=1048576-
        
        # Transcoded stream
        GET /api/v1/stream/{track_id}?transcode=true&bitrate=128
    """
    from app.services.streaming import DEFAULT_BITRATE
    
    # Get track from database
    statement = select(Track).where(Track.id == track_id)
    result = await db.exec(statement)
    track = result.first()
    
    if not track:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Track not found")
    
    file_path = Path(track.file_path)
    
    # Validate bitrate for transcoding
    if transcode:
        bitrate = validate_bitrate(bitrate)
    else:
        bitrate = DEFAULT_BITRATE
    
    # Handle stream request
    status_code, headers, generator = await handle_stream_request(
        track_id=track_id,
        file_path=file_path,
        range_header=range_header,
        transcode=transcode,
        bitrate=bitrate,
    )
    
    # Set correct content type based on track mime type for non-transcoded
    if not transcode:
        headers["Content-Type"] = track.mime_type or "audio/mpeg"
    
    return StreamingResponse(
        generator,
        status_code=status_code,
        headers=headers,
        media_type=headers["Content-Type"],
    )


@router.get("/stream/{track_id}/cache-stats")
async def get_streaming_cache_stats(
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Get streaming cache statistics.
    
    Returns information about:
    - Number of cached entries
    - Total cache size
    - Active transcodes
    - Cache utilization
    """
    stats = await get_cache_stats()
    return stats


@router.get("/stream/docs")
async def get_streaming_docs(
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Get cURL examples for testing streaming endpoints.
    """
    return {
        "description": "cURL examples for testing the streaming API",
        "examples": CURL_EXAMPLES.strip(),
    }
