from sqlmodel import SQLModel, create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.config import settings


# Async engine for database operations
async_engine = create_async_engine(
    settings.database_url,
    echo=settings.environment == "development",
    pool_pre_ping=True,
)

# Async session factory
AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncSession:
    """Dependency to get async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables."""
    from sqlmodel import SQLModel
    from app.models.user import User
    from app.models.track import Track, Album, Artist
    from app.models.playlist import Playlist, PlaylistTrack
    from app.models.session import Session

    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
