from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlmodel import Field, SQLModel, Relationship
import uuid

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.track import Track


class Playlist(SQLModel, table=True):
    __tablename__ = "playlists"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, index=True)
    name: str = Field(index=True)
    description: Optional[str] = None
    owner_id: str = Field(foreign_key="users.id", index=True)
    is_public: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    owner: "User" = Relationship(back_populates="playlists")
    tracks: List["PlaylistTrack"] = Relationship(back_populates="playlist", cascade_delete=True)


class PlaylistTrack(SQLModel, table=True):
    __tablename__ = "playlist_tracks"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, index=True)
    playlist_id: str = Field(foreign_key="playlists.id", index=True)
    track_id: str = Field(foreign_key="tracks.id", index=True)
    position: int = Field(default=0, index=True)

    playlist: "Playlist" = Relationship(back_populates="tracks")
    track: "Track" = Relationship(back_populates="playlist_tracks")
