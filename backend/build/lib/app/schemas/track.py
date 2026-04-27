from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


class TrackBase(BaseModel):
    title: str
    duration_ms: int
    file_path: str
    file_size_bytes: int
    mime_type: str
    bitrate_kbps: int
    sample_rate_hz: int
    channels: int


class TrackCreate(TrackBase):
    album_id: Optional[str] = None
    artist_id: Optional[str] = None


class TrackUpdate(BaseModel):
    title: Optional[str] = None
    album_id: Optional[str] = None
    artist_id: Optional[str] = None


class TrackResponse(TrackBase):
    id: str
    album_id: Optional[str] = None
    artist_id: Optional[str] = None
    play_count: int = 0
    last_played: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TrackListResponse(BaseModel):
    items: List[TrackResponse]
    total: int
    offset: int
    limit: int


class AlbumBase(BaseModel):
    title: str
    release_year: Optional[int] = None
    cover_art_path: Optional[str] = None


class AlbumCreate(AlbumBase):
    artist_id: Optional[str] = None


class AlbumResponse(AlbumBase):
    id: str
    artist_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ArtistBase(BaseModel):
    name: str


class ArtistCreate(ArtistBase):
    pass


class ArtistResponse(ArtistBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True


class TrackSearchRequest(BaseModel):
    q: Optional[str] = None
    artist_id: Optional[str] = None
    album_id: Optional[str] = None
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=50, ge=1, le=200)
    sort: str = "title"
