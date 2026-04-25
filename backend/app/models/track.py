from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel, Relationship
import uuid


class Track(SQLModel, table=True):
    __tablename__ = "tracks"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    title: str = Field(index=True)
    duration_ms: int = Field(ge=0)
    file_path: str = Field(unique=True)
    file_size_bytes: int = Field(ge=0)
    mime_type: str  # audio/mpeg, audio/flac, etc.
    bitrate_kbps: int = Field(ge=0)
    sample_rate_hz: int = Field(ge=0)
    channels: int = Field(ge=1)

    # Full-text search
    search_vector: str = Field(sa_column_kwargs={"index": True})

    album_id: Optional[str] = Field(default=None, foreign_key="albums.id", index=True)
    artist_id: Optional[str] = Field(default=None, foreign_key="artists.id", index=True)

    play_count: int = Field(default=0, ge=0)
    last_played: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    album: Optional["Album"] = Relationship(back_populates="tracks")
    artist: Optional["Artist"] = Relationship(back_populates="tracks")


class Album(SQLModel, table=True):
    __tablename__ = "albums"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    title: str = Field(index=True)
    artist_id: Optional[str] = Field(default=None, foreign_key="artists.id", index=True)
    release_year: Optional[int] = Field(default=None, ge=1900, le=2100)
    cover_art_path: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    artist: Optional["Artist"] = Relationship(back_populates="albums")
    tracks: list["Track"] = Relationship(back_populates="album")


class Artist(SQLModel, table=True):
    __tablename__ = "artists"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str = Field(unique=True, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    albums: list["Album"] = Relationship(back_populates="artist")
    tracks: list["Track"] = Relationship(back_populates="artist")
