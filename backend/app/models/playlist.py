from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel, Relationship
import uuid


class Playlist(SQLModel, table=True):
    __tablename__ = "playlists"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str
    description: Optional[str] = None
    owner_id: str = Field(foreign_key="users.id")
    is_public: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    owner: "User" = Relationship(back_populates="playlists")
    tracks: list["PlaylistTrack"] = Relationship(back_populates="playlist")


class PlaylistTrack(SQLModel, table=True):
    __tablename__ = "playlist_tracks"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    playlist_id: str = Field(foreign_key="playlists.id", index=True)
    track_id: str = Field(foreign_key="tracks.id", index=True)
    position: int

    playlist: Playlist = Relationship(back_populates="tracks")
    track: "Track" = Relationship()
