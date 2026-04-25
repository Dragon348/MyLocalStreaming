#!/usr/bin/env python3
"""
Music library scanner - recursively scans MUSIC_DIR for audio files,
parses ID3 tags using mutagen, and saves/updates records in the database.
"""

import asyncio
import hashlib
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from mutagen import File as MutagenFile
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TRCK, TDRC, APIC
from mutagen.flac import FLAC
from mutagen.oggvorbis import OggVorbis
from sqlalchemy import select
from sqlmodel import SQLModel, create_engine, Session

from app.config import settings
from app.models.track import Track, Album, Artist
from app.database import async_engine, AsyncSessionLocal

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Supported audio extensions
AUDIO_EXTENSIONS = {".mp3", ".flac", ".ogg", ".m4a", ".aac", ".wav", ".wma"}


def get_mime_type(file_path: Path) -> str:
    """Determine MIME type based on file extension."""
    mime_map = {
        ".mp3": "audio/mpeg",
        ".flac": "audio/flac",
        ".ogg": "audio/ogg",
        ".m4a": "audio/mp4",
        ".aac": "audio/aac",
        ".wav": "audio/wav",
        ".wma": "audio/x-ms-wma",
    }
    return mime_map.get(file_path.suffix.lower(), "application/octet-stream")


def normalize_path(path: Path) -> str:
    """Normalize file path for consistent storage."""
    return str(path.resolve())


def parse_id3_tags(file_path: Path) -> dict:
    """Parse ID3 tags from an audio file."""
    tags = {
        "title": None,
        "artist": None,
        "album": None,
        "track_number": None,
        "year": None,
        "duration_ms": None,
        "bitrate_kbps": None,
        "sample_rate_hz": None,
        "channels": None,
        "has_cover": False,
    }
    
    try:
        audio = MutagenFile(str(file_path))
        if audio is None:
            logger.warning(f"Could not read audio file: {file_path}")
            return tags
        
        # Get audio properties
        if audio.info:
            tags["duration_ms"] = int(audio.length * 1000)
            tags["bitrate_kbps"] = int(getattr(audio.info, "bitrate", 0) / 1000)
            tags["sample_rate_hz"] = int(getattr(audio.info, "sample_rate", 0))
            tags["channels"] = int(getattr(audio.info, "channels", 0))
        
        # Parse tags based on file type
        if isinstance(audio, ID3) or (hasattr(audio, "tags") and isinstance(audio.tags, ID3)):
            # MP3 file
            id3_tags = audio.tags if hasattr(audio, "tags") else audio
            
            if id3_tags:
                if TIT2 in id3_tags:
                    tags["title"] = str(id3_tags[TIT2])
                if TPE1 in id3_tags:
                    tags["artist"] = str(id3_tags[TPE1])
                if TALB in id3_tags:
                    tags["album"] = str(id3_tags[TALB])
                if TRCK in id3_tags:
                    track_str = str(id3_tags[TRCK])
                    match = re.match(r"(\d+)", track_str)
                    if match:
                        tags["track_number"] = int(match.group(1))
                if TDRC in id3_tags:
                    year_str = str(id3_tags[TDRC])
                    match = re.match(r"(\d{4})", year_str)
                    if match:
                        tags["year"] = int(match.group(1))
                if APIC in id3_tags:
                    tags["has_cover"] = True
                    
        elif isinstance(audio, FLAC):
            # FLAC file
            if audio.tags:
                tags["title"] = audio.tags.get("title", [None])[0]
                tags["artist"] = audio.tags.get("artist", [None])[0]
                tags["album"] = audio.tags.get("album", [None])[0]
                tags["year"] = audio.tags.get("date", [None])[0]
                track_str = audio.tags.get("tracknumber", [None])[0]
                if track_str:
                    match = re.match(r"(\d+)", str(track_str))
                    if match:
                        tags["track_number"] = int(match.group(1))
                tags["has_cover"] = bool(audio.pictures)
                
        elif isinstance(audio, OggVorbis):
            # OGG Vorbis file
            if audio.tags:
                tags["title"] = audio.tags.get("title", [None])[0]
                tags["artist"] = audio.tags.get("artist", [None])[0]
                tags["album"] = audio.tags.get("album", [None])[0]
                tags["year"] = audio.tags.get("date", [None])[0]
                
    except Exception as e:
        logger.error(f"Error parsing tags from {file_path}: {e}")
    
    return tags


async def get_or_create_artist(session: AsyncSession, name: str) -> Artist:
    """Get existing artist or create new one."""
    result = await session.execute(select(Artist).where(Artist.name == name))
    artist = result.scalar_one_or_none()
    
    if not artist:
        artist = Artist(name=name)
        session.add(artist)
        await session.flush()
    
    return artist


async def get_or_create_album(
    session: AsyncSession,
    title: str,
    artist_id: Optional[str],
    year: Optional[int] = None,
) -> Album:
    """Get existing album or create new one."""
    query = select(Artist).where(Artist.title == title)
    if artist_id:
        query = query.where(Artist.artist_id == artist_id)
    
    result = await session.execute(query)
    album = result.scalar_one_or_none()
    
    if not album:
        album = Album(
            title=title,
            artist_id=artist_id,
            release_year=year,
        )
        session.add(album)
        await session.flush()
    
    return album


async def scan_file(file_path: Path, session: AsyncSession) -> Optional[Track]:
    """Scan a single audio file and save/update track in database."""
    normalized_path = normalize_path(file_path)
    
    # Check if track already exists
    result = await session.execute(
        select(Track).where(Track.file_path == normalized_path)
    )
    existing_track = result.scalar_one_or_none()
    
    try:
        # Parse tags
        tags = parse_id3_tags(file_path)
        
        # Get file stats
        stat = file_path.stat()
        file_size = stat.st_size
        
        # Use filename as fallback title
        title = tags["title"] or file_path.stem
        
        # Get or create artist
        artist = None
        if tags["artist"]:
            artist = await get_or_create_artist(session, tags["artist"])
        
        # Get or create album
        album = None
        if tags["album"]:
            album = await get_or_create_album(
                session,
                tags["album"],
                artist.id if artist else None,
                tags.get("year"),
            )
        
        if existing_track:
            # Update existing track
            existing_track.title = title
            existing_track.duration_ms = tags["duration_ms"] or existing_track.duration_ms
            existing_track.file_size_bytes = file_size
            existing_track.mime_type = get_mime_type(file_path)
            existing_track.bitrate_kbps = tags["bitrate_kbps"] or existing_track.bitrate_kbps
            existing_track.sample_rate_hz = tags["sample_rate_hz"] or existing_track.sample_rate_hz
            existing_track.channels = tags["channels"] or existing_track.channels
            existing_track.album_id = album.id if album else None
            existing_track.artist_id = artist.id if artist else None
            existing_track.updated_at = datetime.utcnow()
            
            track = existing_track
        else:
            # Create new track
            track = Track(
                title=title,
                duration_ms=tags["duration_ms"] or 0,
                file_path=normalized_path,
                file_size_bytes=file_size,
                mime_type=get_mime_type(file_path),
                bitrate_kbps=tags["bitrate_kbps"] or 0,
                sample_rate_hz=tags["sample_rate_hz"] or 0,
                channels=tags["channels"] or 0,
                search_vector=title,  # Simple search vector
                album_id=album.id if album else None,
                artist_id=artist.id if artist else None,
            )
            session.add(track)
        
        await session.flush()
        logger.info(f"Processed: {file_path} -> {title}")
        return track
        
    except Exception as e:
        logger.error(f"Error processing {file_path}: {e}")
        if existing_track:
            # Mark as potentially broken
            existing_track.updated_at = datetime.utcnow()
        return None


async def scan_directory(music_dir: Path, session: AsyncSession) -> dict:
    """Recursively scan directory for audio files."""
    stats = {
        "scanned": 0,
        "added": 0,
        "updated": 0,
        "errors": 0,
    }
    
    # Get all existing tracks to detect deleted files
    result = await session.execute(select(Track))
    existing_tracks = {t.file_path: t for t in result.scalars().all()}
    
    scanned_files = set()
    
    # Walk through directory
    for root, dirs, files in os.walk(music_dir):
        for filename in files:
            file_path = Path(root) / filename
            
            if file_path.suffix.lower() not in AUDIO_EXTENSIONS:
                continue
            
            stats["scanned"] += 1
            scanned_files.add(normalize_path(file_path))
            
            # Check if it's a new or existing file
            was_existing = normalize_path(file_path) in existing_tracks
            
            track = await scan_file(file_path, session)
            
            if track:
                if was_existing:
                    stats["updated"] += 1
                else:
                    stats["added"] += 1
            else:
                stats["errors"] += 1
    
    # Handle deleted files
    deleted_paths = set(existing_tracks.keys()) - scanned_files
    for path in deleted_paths:
        track = existing_tracks[path]
        await session.delete(track)
        logger.info(f"Deleted track (file missing): {path}")
    
    await session.commit()
    
    return stats


async def main():
    """Main entry point for the scanner."""
    music_dir = Path(settings.music_dir)
    
    if not music_dir.exists():
        logger.error(f"Music directory does not exist: {music_dir}")
        return
    
    logger.info(f"Starting scan of {music_dir}")
    
    async with AsyncSessionLocal() as session:
        try:
            stats = await scan_directory(music_dir, session)
            logger.info(f"Scan complete: {stats}")
        except Exception as e:
            logger.error(f"Scan failed: {e}")
            await session.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(main())
