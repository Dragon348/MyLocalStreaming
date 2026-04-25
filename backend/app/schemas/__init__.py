"""Schemas for request/response validation."""

from app.schemas.auth import (
    UserCreate,
    UserLogin,
    Token,
    TokenData,
    UserResponse,
)
from app.schemas.track import (
    TrackBase,
    TrackCreate,
    TrackUpdate,
    TrackResponse,
    AlbumBase,
    AlbumCreate,
    AlbumResponse,
    ArtistBase,
    ArtistCreate,
    ArtistResponse,
    TrackListResponse,
)
from app.schemas.playlist import (
    PlaylistBase,
    PlaylistCreate,
    PlaylistUpdate,
    PlaylistResponse,
    PlaylistTrackAdd,
    PlaylistTrackResponse,
    PlaylistDetailResponse,
)

__all__ = [
    # Auth
    "UserCreate",
    "UserLogin",
    "Token",
    "TokenData",
    "UserResponse",
    # Tracks
    "TrackBase",
    "TrackCreate",
    "TrackUpdate",
    "TrackResponse",
    "AlbumBase",
    "AlbumCreate",
    "AlbumResponse",
    "ArtistBase",
    "ArtistCreate",
    "ArtistResponse",
    "TrackListResponse",
    # Playlists
    "PlaylistBase",
    "PlaylistCreate",
    "PlaylistUpdate",
    "PlaylistResponse",
    "PlaylistTrackAdd",
    "PlaylistTrackResponse",
    "PlaylistDetailResponse",
]