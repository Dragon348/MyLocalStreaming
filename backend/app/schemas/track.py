"""Track schemas for request/response validation."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class TrackBase(BaseModel):
    """Base schema for track data."""

    title: str = Field(..., min_length=1, max_length=255)
    duration_ms: int = Field(..., ge=0)
    file_path: str
    file_size_bytes: int = Field(..., ge=0)
    mime_type: str
    bitrate_kbps: int = Field(..., ge=0)
    sample_rate_hz: int = Field(..., ge=0)
    channels: int = Field(..., ge=1)


class TrackCreate(TrackBase):
    """Schema for creating a track."""

    album_id: Optional[str] = None
    artist_id: Optional[str] = None


class TrackUpdate(BaseModel):
    """Schema for updating a track."""

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    duration_ms: Optional[int] = Field(None, ge=0)
    album_id: Optional[str] = None
    artist_id: Optional[str] = None


class TrackResponse(TrackBase):
    """Schema for track response."""

    id: str
    album_id: Optional[str] = None
    artist_id: Optional[str] = None
    play_count: int = 0
    last_played: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AlbumBase(BaseModel):
    """Base schema for album data."""

    title: str = Field(..., min_length=1, max_length=255)
    release_year: Optional[int] = Field(None, ge=1900, le=2100)
    cover_art_path: Optional[str] = None


class AlbumCreate(AlbumBase):
    """Schema for creating an album."""

    artist_id: Optional[str] = None


class AlbumResponse(AlbumBase):
    """Schema for album response."""

    id: str
    artist_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ArtistBase(BaseModel):
    """Base schema for artist data."""

    name: str = Field(..., min_length=1, max_length=255)


class ArtistCreate(ArtistBase):
    """Schema for creating an artist."""

    pass


class ArtistResponse(ArtistBase):
    """Schema for artist response."""

    id: str
    created_at: datetime

    class Config:
        from_attributes = True


class TrackListResponse(BaseModel):
    """Paginated list of tracks."""

    items: list[TrackResponse]
    total: int
    page: int
    page_size: int
    pages: int
