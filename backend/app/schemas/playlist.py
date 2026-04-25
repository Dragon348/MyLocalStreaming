"""Playlist schemas for request/response validation."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class PlaylistBase(BaseModel):
    """Base schema for playlist data."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    is_public: bool = False


class PlaylistCreate(PlaylistBase):
    """Schema for creating a playlist."""

    pass


class PlaylistUpdate(BaseModel):
    """Schema for updating a playlist."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    is_public: Optional[bool] = None


class PlaylistResponse(PlaylistBase):
    """Schema for playlist response."""

    id: str
    owner_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PlaylistTrackAdd(BaseModel):
    """Schema for adding a track to a playlist."""

    track_id: str
    position: Optional[int] = None


class PlaylistTrackResponse(BaseModel):
    """Schema for playlist track response."""

    id: str
    playlist_id: str
    track_id: str
    position: int

    class Config:
        from_attributes = True


class PlaylistDetailResponse(PlaylistResponse):
    """Detailed playlist response with tracks."""

    tracks: list[PlaylistTrackResponse] = []
