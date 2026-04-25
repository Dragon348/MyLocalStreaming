from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db


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

    return app


app = create_app()
