import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.track import Track, Album, Artist
from app.services.metadata_parser import MetadataParser

logger = logging.getLogger(__name__)


class LibraryScanner:
    """Recursively scan music directory and update database."""

    def __init__(self, music_dir: str, db: AsyncSession):
        self.music_dir = Path(music_dir)
        self.db = db
        self.stats = {
            "scanned": 0,
            "added": 0,
            "updated": 0,
            "errors": 0,
            "skipped": 0,
        }

    async def scan(self, force_rescan: bool = False) -> Dict[str, Any]:
        """
        Scan the music directory and update the database.

        Args:
            force_rescan: If True, re-parse all files even if they exist in DB.

        Returns:
            Statistics about the scan operation.
        """
        logger.info(f"Starting library scan of {self.music_dir}")

        if not self.music_dir.exists():
            logger.error(f"Music directory does not exist: {self.music_dir}")
            return self.stats

        # Get existing file paths from DB for quick lookup
        existing_tracks = await self._get_existing_tracks()

        # Recursively find all audio files
        audio_files = self._find_audio_files()

        for file_path in audio_files:
            try:
                await self._process_file(file_path, existing_tracks, force_rescan)
            except Exception as e:
                logger.exception(f"Error processing {file_path}: {e}")
                self.stats["errors"] += 1

        # Clean up tracks that no longer exist (optional - could be configurable)
        if not force_rescan:
            await self._cleanup_missing_tracks(existing_tracks)

        logger.info(f"Library scan completed: {self.stats}")
        return self.stats

    async def _get_existing_tracks(self) -> Dict[str, Track]:
        """Get all existing tracks from database indexed by file path."""
        statement = select(Track)
        result = await self.db.exec(statement)
        tracks = result.all()
        return {track.file_path: track for track in tracks}

    def _find_audio_files(self) -> List[Path]:
        """Recursively find all supported audio files."""
        audio_files = []

        try:
            for item in self.music_dir.rglob("*"):
                if item.is_file() and MetadataParser.is_audio_file(item):
                    # Normalize path
                    normalized_path = item.resolve()
                    audio_files.append(normalized_path)
        except PermissionError as e:
            logger.warning(f"Permission denied accessing directory: {e}")

        return audio_files

    async def _process_file(
        self,
        file_path: Path,
        existing_tracks: Dict[str, Track],
        force_rescan: bool,
    ) -> None:
        """Process a single audio file."""
        file_path_str = str(file_path)
        self.stats["scanned"] += 1

        # Check if already in database
        existing_track = existing_tracks.get(file_path_str)

        if existing_track and not force_rescan:
            # Check if file was modified
            try:
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if mtime <= existing_track.updated_at:
                    self.stats["skipped"] += 1
                    return
            except Exception:
                pass

        # Parse metadata
        metadata = MetadataParser.parse_file(file_path)
        if not metadata:
            logger.warning(f"Could not parse metadata for {file_path}")
            self.stats["errors"] += 1
            return

        # Get or create artist
        artist_id = None
        if metadata.get("artist"):
            artist_id = await self._get_or_create_artist(metadata["artist"])

        # Get or create album
        album_id = None
        if metadata.get("album") or artist_id:
            album_id = await self._get_or_create_album(
                title=metadata.get("album", "Unknown Album"),
                artist_id=artist_id,
                release_year=metadata.get("release_year"),
            )

        # Create or update track
        if existing_track:
            await self._update_track(existing_track, metadata, artist_id, album_id)
            self.stats["updated"] += 1
        else:
            await self._create_track(file_path_str, metadata, artist_id, album_id)
            self.stats["added"] += 1

    async def _get_or_create_artist(self, name: str) -> str:
        """Get existing artist or create new one."""
        statement = select(Artist).where(Artist.name == name)
        result = await self.db.exec(statement)
        artist = result.first()

        if not artist:
            artist = Artist(name=name)
            self.db.add(artist)
            await self.db.flush()
            logger.debug(f"Created new artist: {name}")

        return artist.id

    async def _get_or_create_album(
        self,
        title: str,
        artist_id: Optional[str] = None,
        release_year: Optional[int] = None,
    ) -> Optional[str]:
        """Get existing album or create new one."""
        if not title or title == "Unknown Album":
            return None

        statement = select(Album).where(
            (Album.title == title) & (Album.artist_id == artist_id)
        )
        result = await self.db.exec(statement)
        album = result.first()

        if not album:
            album = Album(
                title=title,
                artist_id=artist_id,
                release_year=release_year,
            )
            self.db.add(album)
            await self.db.flush()
            logger.debug(f"Created new album: {title}")

        return album.id

    async def _update_track(
        self,
        track: Track,
        metadata: Dict[str, Any],
        artist_id: Optional[str],
        album_id: Optional[str],
    ) -> None:
        """Update an existing track with new metadata."""
        track.title = metadata["title"]
        track.duration_ms = metadata["duration_ms"]
        track.file_size_bytes = metadata["file_size_bytes"]
        track.mime_type = metadata["mime_type"]
        track.bitrate_kbps = metadata["bitrate_kbps"]
        track.sample_rate_hz = metadata["sample_rate_hz"]
        track.channels = metadata["channels"]
        track.artist_id = artist_id
        track.album_id = album_id
        track.updated_at = datetime.utcnow()

        logger.debug(f"Updated track: {track.title}")

    async def _create_track(
        self,
        file_path_str: str,
        metadata: Dict[str, Any],
        artist_id: Optional[str],
        album_id: Optional[str],
    ) -> None:
        """Create a new track entry."""
        track = Track(
            title=metadata["title"],
            duration_ms=metadata["duration_ms"],
            file_path=file_path_str,
            file_size_bytes=metadata["file_size_bytes"],
            mime_type=metadata["mime_type"],
            bitrate_kbps=metadata["bitrate_kbps"],
            sample_rate_hz=metadata["sample_rate_hz"],
            channels=metadata["channels"],
            artist_id=artist_id,
            album_id=album_id,
            search_vector=f"{metadata['title']} {metadata.get('artist', '')} {metadata.get('album', '')}".lower(),
        )
        self.db.add(track)
        logger.debug(f"Created new track: {track.title}")

    async def _cleanup_missing_tracks(self, existing_tracks: Dict[str, Track]) -> None:
        """Remove tracks from database that no longer exist on disk."""
        current_files = set(str(f) for f in self._find_audio_files())

        to_delete = []
        for file_path, track in existing_tracks.items():
            if file_path not in current_files:
                to_delete.append(track)

        if to_delete:
            logger.info(f"Removing {len(to_delete)} tracks that no longer exist")
            for track in to_delete:
                self.db.delete(track)
            await self.db.commit()
