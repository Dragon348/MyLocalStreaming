"""API module initialization."""

from app.api.auth import router as auth_router
from app.api.tracks import router as tracks_router
from app.api.playlists import router as playlists_router

__all__ = ["auth_router", "tracks_router", "playlists_router"]