from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


class PlaylistBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None


class PlaylistCreate(PlaylistBase):
    is_public: bool = False


class PlaylistUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    is_public: Optional[bool] = None


class PlaylistTrackAdd(BaseModel):
    track_id: str


class PlaylistTrackReorder(BaseModel):
    track_id: str
    position: int


class PlaylistResponse(PlaylistBase):
    id: str
    owner_id: str
    is_public: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PlaylistTrackResponse(BaseModel):
    id: str
    playlist_id: str
    track_id: str
    position: int

    class Config:
        from_attributes = True


class PlaylistWithTracksResponse(PlaylistResponse):
    tracks: List[PlaylistTrackResponse] = []


class PlaylistListResponse(BaseModel):
    items: List[PlaylistResponse]
    total: int
    offset: int
    limit: int
