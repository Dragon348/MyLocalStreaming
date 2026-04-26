#!/usr/bin/env python3
"""
Library scanner script - scans music directory and updates database.

Usage:
    python scanner.py [--music-dir /path/to/music] [--force-rescan]
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models.user import User
from app.models.track import Track, Album, Artist
from app.models.playlist import Playlist, PlaylistTrack
from app.models.session import Session
from app.services.library_scanner import LibraryScanner

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def init_database(database_url: str) -> AsyncSession:
    """Initialize database connection."""
    engine = create_async_engine(
        database_url,
        echo=False,
        pool_pre_ping=True,
    )

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    AsyncSessionLocal = sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    return AsyncSessionLocal()


async def scan_library(music_dir: str, force_rescan: bool = False) -> dict:
    """Scan the music library and update database."""
    logger.info(f"Starting library scan of: {music_dir}")
    logger.info(f"Force rescan: {force_rescan}")

    db = await init_database(settings.database_url)

    try:
        scanner = LibraryScanner(music_dir=music_dir, db=db)
        stats = await scanner.scan(force_rescan=force_rescan)

        # Commit any remaining changes
        await db.commit()

        return stats

    except Exception as e:
        logger.exception(f"Error during library scan: {e}")
        await db.rollback()
        raise
    finally:
        await db.close()


def main():
    parser = argparse.ArgumentParser(description="Scan music library")
    parser.add_argument(
        "--music-dir",
        type=str,
        default=settings.music_dir,
        help=f"Path to music directory (default: {settings.music_dir})",
    )
    parser.add_argument(
        "--force-rescan",
        action="store_true",
        help="Force re-scan all files even if they exist in database",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level",
    )

    args = parser.parse_args()

    # Set log level
    logging.getLogger().setLevel(args.log_level)

    # Validate music directory
    music_path = Path(args.music_dir)
    if not music_path.exists():
        logger.error(f"Music directory does not exist: {music_path}")
        sys.exit(1)

    if not music_path.is_dir():
        logger.error(f"Music path is not a directory: {music_path}")
        sys.exit(1)

    # Run scanner
    try:
        stats = asyncio.run(scan_library(args.music_dir, args.force_rescan))

        print("\n" + "=" * 50)
        print("Library Scan Complete!")
        print("=" * 50)
        print(f"Files scanned:  {stats['scanned']}")
        print(f"Added:          {stats['added']}")
        print(f"Updated:        {stats['updated']}")
        print(f"Skipped:        {stats['skipped']}")
        print(f"Errors:         {stats['errors']}")
        print("=" * 50)

    except Exception as e:
        logger.error(f"Scan failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
