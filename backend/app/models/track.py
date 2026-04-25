from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel, Relationship
import uuid


class Track(SQLModel, table=True):
    __tablename__ = "tracks"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    title: str = Field(index=True)
    duration_ms: int
    file_path: str = Field(unique=True)
    file_size_bytes: int
    mime_type: str  # audio/mpeg, audio/flac, etc.
    bitrate_kbps: int
    sample_rate_hz: int
    channels: int

    # Full-text search
    search_vector: str = Field(sa_column_kwargs={"index": True})

    album_id: Optional[str] = Field(default=None, foreign_key="albums.id")
    artist_id: Optional[str] = Field(default=None, foreign_key="artists.id")

    play_count: int = Field(default=0)
    last_played: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    album: Optional["Album"] = Relationship(back_populates="tracks")
    artist: Optional["Artist"] = Relationship(back_populates="tracks")


class Album(SQLModel, table=True):
    __tablename__ = "albums"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    title: str = Field(index=True)
    artist_id: Optional[str] = Field(default=None, foreign_key="artists.id")
    release_year: Optional[int] = None
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
