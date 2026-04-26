from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.playlist import Playlist, PlaylistTrack
from app.models.user import User
from app.schemas.playlist import (
    PlaylistCreate,
    PlaylistResponse,
    PlaylistUpdate,
    PlaylistTrackAdd,
    PlaylistWithTracksResponse,
    PlaylistListResponse,
)
from app.utils.deps import get_current_user

router = APIRouter(prefix="/playlists", tags=["Playlists"])


@router.get("", response_model=PlaylistListResponse)
async def list_playlists(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List all playlists for the current user."""
    # Build query - show user's playlists and public playlists
    statement = select(Playlist).where(
        (Playlist.owner_id == current_user.id) | (Playlist.is_public == True)
    )

    # Get total count
    count_statement = select(func.count(Playlist.id)).where(
        (Playlist.owner_id == current_user.id) | (Playlist.is_public == True)
    )
    total_result = await db.exec(count_statement)
    total = total_result.one()

    # Apply pagination
    statement = statement.order_by(Playlist.name).offset(offset).limit(limit)
    result = await db.exec(statement)
    playlists = result.all()

    return {
        "items": playlists,
        "total": total,
        "offset": offset,
        "limit": limit,
    }


@router.post("", response_model=PlaylistResponse, status_code=status.HTTP_201_CREATED)
async def create_playlist(
    playlist_data: PlaylistCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Playlist:
    """Create a new playlist."""
    playlist = Playlist(
        name=playlist_data.name,
        description=playlist_data.description,
        owner_id=current_user.id,
        is_public=playlist_data.is_public,
    )

    db.add(playlist)
    await db.commit()
    await db.refresh(playlist)

    return playlist


@router.get("/{playlist_id}", response_model=PlaylistWithTracksResponse)
async def get_playlist(
    playlist_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Playlist:
    """Get a specific playlist with its tracks."""
    statement = select(Playlist).where(Playlist.id == playlist_id)
    result = await db.exec(statement)
    playlist = result.first()

    if not playlist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playlist not found")

    # Check permissions
    if playlist.owner_id != current_user.id and not playlist.is_public:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this playlist",
        )

    return playlist


@router.put("/{playlist_id}", response_model=PlaylistResponse)
async def update_playlist(
    playlist_id: str,
    playlist_data: PlaylistUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Playlist:
    """Update a playlist."""
    statement = select(Playlist).where(Playlist.id == playlist_id)
    result = await db.exec(statement)
    playlist = result.first()

    if not playlist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playlist not found")

    # Check ownership
    if playlist.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to edit this playlist",
        )

    # Update fields
    update_data = playlist_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(playlist, field, value)

    await db.commit()
    await db.refresh(playlist)

    return playlist


@router.delete("/{playlist_id}")
async def delete_playlist(
    playlist_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Delete a playlist."""
    statement = select(Playlist).where(Playlist.id == playlist_id)
    result = await db.exec(statement)
    playlist = result.first()

    if not playlist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playlist not found")

    # Check ownership
    if playlist.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this playlist",
        )

    db.delete(playlist)
    await db.commit()

    return {"message": "Playlist deleted successfully"}


@router.post("/{playlist_id}/tracks", response_model=PlaylistWithTracksResponse)
async def add_track_to_playlist(
    playlist_id: str,
    track_data: PlaylistTrackAdd,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Playlist:
    """Add a track to a playlist."""
    # Get playlist
    statement = select(Playlist).where(Playlist.id == playlist_id)
    result = await db.exec(statement)
    playlist = result.first()

    if not playlist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playlist not found")

    # Check ownership
    if playlist.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to modify this playlist",
        )

    # Get max position
    max_pos_statement = select(func.max(PlaylistTrack.position)).where(
        PlaylistTrack.playlist_id == playlist_id
    )
    max_pos_result = await db.exec(max_pos_statement)
    max_position = max_pos_result.one() or 0

    # Check if track already exists in playlist
    existing_statement = select(PlaylistTrack).where(
        (PlaylistTrack.playlist_id == playlist_id) & (PlaylistTrack.track_id == track_data.track_id)
    )
    existing_result = await db.exec(existing_statement)
    if existing_result.first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Track already in playlist",
        )

    # Add track
    playlist_track = PlaylistTrack(
        playlist_id=playlist_id,
        track_id=track_data.track_id,
        position=max_position + 1,
    )
    db.add(playlist_track)
    await db.commit()
    await db.refresh(playlist)

    return playlist


@router.delete("/{playlist_id}/tracks/{track_id}")
async def remove_track_from_playlist(
    playlist_id: str,
    track_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Remove a track from a playlist."""
    # Get playlist
    statement = select(Playlist).where(Playlist.id == playlist_id)
    result = await db.exec(statement)
    playlist = result.first()

    if not playlist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playlist not found")

    # Check ownership
    if playlist.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to modify this playlist",
        )

    # Find and delete playlist track
    statement = select(PlaylistTrack).where(
        (PlaylistTrack.playlist_id == playlist_id) & (PlaylistTrack.track_id == track_id)
    )
    result = await db.exec(statement)
    playlist_track = result.first()

    if not playlist_track:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Track not found in playlist",
        )

    db.delete(playlist_track)
    await db.commit()

    return {"message": "Track removed from playlist"}


@router.put("/{playlist_id}/reorder", response_model=PlaylistWithTracksResponse)
async def reorder_playlist_tracks(
    playlist_id: str,
    track_data: PlaylistTrackAdd,
    position: int = Query(..., ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Playlist:
    """Reorder tracks in a playlist."""
    # Get playlist
    statement = select(Playlist).where(Playlist.id == playlist_id)
    result = await db.exec(statement)
    playlist = result.first()

    if not playlist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playlist not found")

    # Check ownership
    if playlist.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to modify this playlist",
        )

    # Find the track
    statement = select(PlaylistTrack).where(
        (PlaylistTrack.playlist_id == playlist_id) & (PlaylistTrack.track_id == track_data.track_id)
    )
    result = await db.exec(statement)
    playlist_track = result.first()

    if not playlist_track:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Track not found in playlist",
        )

    # Update position
    playlist_track.position = position
    await db.commit()
    await db.refresh(playlist)

    return playlist
