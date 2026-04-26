from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlmodel import Field, SQLModel, Relationship
import uuid

if TYPE_CHECKING:
    from app.models.playlist import PlaylistTrack


class Track(SQLModel, table=True):
    __tablename__ = "tracks"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, index=True)
    title: str = Field(index=True)
    duration_ms: int
    file_path: str = Field(unique=True, index=True)
    file_size_bytes: int
    mime_type: str
    bitrate_kbps: int
    sample_rate_hz: int
    channels: int
    search_vector: str = Field(sa_column_kwargs={"index": True})

    album_id: Optional[str] = Field(default=None, foreign_key="albums.id", index=True)
    artist_id: Optional[str] = Field(default=None, foreign_key="artists.id", index=True)

    play_count: int = Field(default=0, index=True)
    last_played: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    album: Optional["Album"] = Relationship(back_populates="tracks")
    artist: Optional["Artist"] = Relationship(back_populates="tracks")
    playlist_tracks: List["PlaylistTrack"] = Relationship(back_populates="track", cascade_delete=True)


class Album(SQLModel, table=True):
    __tablename__ = "albums"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, index=True)
    title: str = Field(index=True)
    artist_id: Optional[str] = Field(default=None, foreign_key="artists.id", index=True)
    release_year: Optional[int] = None
    cover_art_path: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    artist: Optional["Artist"] = Relationship(back_populates="albums")
    tracks: List["Track"] = Relationship(back_populates="album")


class Artist(SQLModel, table=True):
    __tablename__ = "artists"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, index=True)
    name: str = Field(unique=True, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    albums: List["Album"] = Relationship(back_populates="artist")
    tracks: List["Track"] = Relationship(back_populates="artist")
