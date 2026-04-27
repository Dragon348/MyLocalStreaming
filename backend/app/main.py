from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.api.auth import router as auth_router
from app.api.tracks import router as tracks_router
from app.api.playlists import router as playlists_router
from app.api.admin import router as admin_router


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(
        title="Music Streaming API",
        description="Music streaming service for family use",
        version="1.0.0",
        docs_url="/docs",
        openapi_url="/openapi.json",
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, specify allowed origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    async def startup_event():
        """Initialize database on startup."""
        await init_db()

    @app.get("/health")
    async def healthcheck():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "environment": settings.environment,
        }

    # Include routers with API versioning
    # Роутеры уже содержат свои префиксы (/auth, /tracks, /playlists) внутри файлов
    app.include_router(auth_router, prefix="/api/v1")  # -> /api/v1/auth
    app.include_router(tracks_router, prefix="/api/v1")  # -> /api/v1/tracks
    app.include_router(playlists_router, prefix="/api/v1")  # -> /api/v1/playlists
    app.include_router(admin_router, prefix="/api/v1")  # -> /api/v1/admin

    return app


app = create_app()
