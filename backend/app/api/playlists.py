"""Playlists API endpoints with CRUD and track management."""

from typing import Annotated, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.schemas.playlist import (
    PlaylistCreate,
    PlaylistUpdate,
    PlaylistResponse,
    PlaylistDetailResponse,
    PlaylistTrackAdd,
    PlaylistTrackResponse,
)
from app.models.playlist import Playlist, PlaylistTrack
from app.models.track import Track
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/playlists", tags=["Playlists"])


@router.get("", response_model=list[PlaylistResponse])
async def list_playlists(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    owner_id: Optional[str] = Query(None, description="Filter by owner ID"),
    include_public: bool = Query(True, description="Include public playlists from other users"),
):
    """List playlists with optional filtering."""
    query = select(Playlist)
    
    filters = []
    if owner_id:
        filters.append(Playlist.owner_id == owner_id)
    elif not include_public:
        # Only show user's own playlists
        filters.append(Playlist.owner_id == current_user.id)
    else:
        # Show user's playlists + public playlists
        filters.append(
            (Playlist.owner_id == current_user.id) | (Playlist.is_public == True)
        )
    
    if filters:
        query = query.where(*filters)
    
    # Order by updated_at descending
    query = query.order_by(Playlist.updated_at.desc())
    
    result = await db.execute(query)
    playlists = result.scalars().all()
    
    return [PlaylistResponse.model_validate(p) for p in playlists]


@router.post("", response_model=PlaylistResponse, status_code=status.HTTP_201_CREATED)
async def create_playlist(
    playlist_data: PlaylistCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Create a new playlist."""
    playlist = Playlist(
        name=playlist_data.name,
        description=playlist_data.description,
        is_public=playlist_data.is_public,
        owner_id=current_user.id,
    )
    
    db.add(playlist)
    await db.commit()
    await db.refresh(playlist)
    
    return playlist


@router.get("/{playlist_id}", response_model=PlaylistDetailResponse)
async def get_playlist(
    playlist_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get a specific playlist with its tracks."""
    result = await db.execute(select(Playlist).where(Playlist.id == playlist_id))
    playlist = result.scalar_one_or_none()
    
    if not playlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playlist not found"
        )
    
    # Check permissions
    if playlist.owner_id != current_user.id and not playlist.is_public:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this playlist"
        )
    
    # Get playlist tracks
    tracks_result = await db.execute(
        select(PlaylistTrack)
        .where(PlaylistTrack.playlist_id == playlist_id)
        .order_by(PlaylistTrack.position)
    )
    playlist_tracks = tracks_result.scalars().all()
    
    response = PlaylistDetailResponse.model_validate(playlist)
    response.tracks = [PlaylistTrackResponse.model_validate(pt) for pt in playlist_tracks]
    
    return response


@router.put("/{playlist_id}", response_model=PlaylistResponse)
async def update_playlist(
    playlist_id: str,
    playlist_data: PlaylistUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Update a playlist."""
    result = await db.execute(select(Playlist).where(Playlist.id == playlist_id))
    playlist = result.scalar_one_or_none()
    
    if not playlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playlist not found"
        )
    
    # Check ownership
    if playlist.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to edit this playlist"
        )
    
    # Update fields
    if playlist_data.name is not None:
        playlist.name = playlist_data.name
    if playlist_data.description is not None:
        playlist.description = playlist_data.description
    if playlist_data.is_public is not None:
        playlist.is_public = playlist_data.is_public
    
    playlist.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(playlist)
    
    return playlist


@router.delete("/{playlist_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_playlist(
    playlist_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Delete a playlist."""
    result = await db.execute(select(Playlist).where(Playlist.id == playlist_id))
    playlist = result.scalar_one_or_none()
    
    if not playlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playlist not found"
        )
    
    # Check ownership
    if playlist.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this playlist"
        )
    
    await db.delete(playlist)
    await db.commit()
    
    return None


@router.post("/{playlist_id}/tracks", response_model=PlaylistTrackResponse)
async def add_track_to_playlist(
    playlist_id: str,
    track_data: PlaylistTrackAdd,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Add a track to a playlist."""
    # Verify playlist exists and user owns it
    result = await db.execute(select(Playlist).where(Playlist.id == playlist_id))
    playlist = result.scalar_one_or_none()
    
    if not playlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playlist not found"
        )
    
    if playlist.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to modify this playlist"
        )
    
    # Verify track exists
    track_result = await db.execute(select(Track).where(Track.id == track_data.track_id))
    track = track_result.scalar_one_or_none()
    
    if not track:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Track not found"
        )
    
    # Determine position
    if track_data.position is None:
        # Get max position
        max_pos_result = await db.execute(
            select(func.max(PlaylistTrack.position)).where(
                PlaylistTrack.playlist_id == playlist_id
            )
        )
        max_position = max_pos_result.scalar() or -1
        position = max_position + 1
    else:
        position = track_data.position
    
    # Create playlist track
    playlist_track = PlaylistTrack(
        playlist_id=playlist_id,
        track_id=track_data.track_id,
        position=position,
    )
    
    db.add(playlist_track)
    playlist.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(playlist_track)
    
    return playlist_track


@router.delete("/{playlist_id}/tracks/{track_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_track_from_playlist(
    playlist_id: str,
    track_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Remove a track from a playlist."""
    # Verify playlist exists and user owns it
    result = await db.execute(select(Playlist).where(Playlist.id == playlist_id))
    playlist = result.scalar_one_or_none()
    
    if not playlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playlist not found"
        )
    
    if playlist.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to modify this playlist"
        )
    
    # Find and delete the playlist track
    pt_result = await db.execute(
        select(PlaylistTrack).where(
            (PlaylistTrack.playlist_id == playlist_id) &
            (PlaylistTrack.track_id == track_id)
        )
    )
    playlist_track = pt_result.scalar_one_or_none()
    
    if not playlist_track:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Track not found in playlist"
        )
    
    await db.delete(playlist_track)
    playlist.updated_at = datetime.utcnow()
    await db.commit()
    
    return None
