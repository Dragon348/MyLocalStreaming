import logging
from pathlib import Path
from typing import Optional, Dict, Any
import mimetypes

from mutagen import File as MutagenFile
from mutagen.id3 import ID3
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.oggvorbis import OggVorbis
from mutagen.mp4 import MP4

logger = logging.getLogger(__name__)


class MetadataParser:
    """Parse audio file metadata using mutagen."""

    AUDIO_MIME_TYPES = {
        ".mp3": "audio/mpeg",
        ".flac": "audio/flac",
        ".ogg": "audio/ogg",
        ".m4a": "audio/mp4",
        ".aac": "audio/aac",
        ".wav": "audio/wav",
    }

    SUPPORTED_EXTENSIONS = set(AUDIO_MIME_TYPES.keys())

    @classmethod
    def is_audio_file(cls, file_path: Path) -> bool:
        """Check if a file is a supported audio file."""
        return file_path.suffix.lower() in cls.SUPPORTED_EXTENSIONS

    @classmethod
    def parse_file(cls, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Parse metadata from an audio file.

        Returns dict with:
            - title, artist, album
            - duration_ms
            - file_size_bytes
            - mime_type
            - bitrate_kbps
            - sample_rate_hz
            - channels
            - track_number, release_year
            - cover_art_path (if found)

        Returns None if file cannot be parsed.
        """
        try:
            if not file_path.exists():
                logger.error(f"File does not exist: {file_path}")
                return None

            audio = MutagenFile(file_path)
            if audio is None:
                logger.warning(f"Could not parse audio file: {file_path}")
                return None

            # Get basic file info
            file_size = file_path.stat().st_size
            mime_type = cls._get_mime_type(file_path)

            # Get audio properties
            info = audio.info
            duration_ms = int(info.length * 1000) if hasattr(info, "length") else 0
            sample_rate = info.sample_rate if hasattr(info, "sample_rate") else 0
            channels = info.channels if hasattr(info, "channels") else 0
            bitrate = cls._get_bitrate(audio, file_size, duration_ms)

            # Get tags
            tags = cls._extract_tags(audio, file_path)

            return {
                "title": tags.get("title", file_path.stem),
                "artist": tags.get("artist"),
                "album": tags.get("album"),
                "duration_ms": duration_ms,
                "file_size_bytes": file_size,
                "mime_type": mime_type,
                "bitrate_kbps": bitrate,
                "sample_rate_hz": sample_rate,
                "channels": channels,
                "track_number": tags.get("track_number"),
                "release_year": tags.get("year"),
                "cover_art": tags.get("cover_art"),
            }

        except Exception as e:
            logger.exception(f"Error parsing file {file_path}: {e}")
            return None

    @classmethod
    def _get_mime_type(cls, file_path: Path) -> str:
        """Get MIME type based on file extension."""
        ext = file_path.suffix.lower()
        return cls.AUDIO_MIME_TYPES.get(ext, "application/octet-stream")

    @classmethod
    def _get_bitrate(cls, audio: Any, file_size: int, duration_ms: int) -> int:
        """Calculate or get bitrate in kbps."""
        # Try to get bitrate from audio info
        if hasattr(audio.info, "bitrate"):
            return int(audio.info.bitrate / 1000)

        # Calculate from file size and duration
        if duration_ms > 0:
            return int((file_size * 8) / (duration_ms * 1000))

        return 0

    @classmethod
    def _extract_tags(cls, audio: Any, file_path: Path) -> Dict[str, Any]:
        """Extract tags from audio file."""
        tags = {}

        try:
            if audio.tags is None:
                return tags

            # Handle different formats
            if isinstance(audio, MP3) or isinstance(audio.tags, ID3):
                tags = cls._parse_id3_tags(audio.tags)
            elif isinstance(audio, FLAC):
                tags = cls._parse_vorbis_tags(audio.tags)
            elif isinstance(audio, OggVorbis):
                tags = cls._parse_vorbis_tags(audio.tags)
            elif isinstance(audio, MP4):
                tags = cls._parse_mp4_tags(audio.tags)
            elif hasattr(audio.tags, "get"):
                # Generic tag handling
                tags = cls._parse_generic_tags(audio.tags)

        except Exception as e:
            logger.warning(f"Error extracting tags from {file_path}: {e}")

        return tags

    @classmethod
    def _parse_id3_tags(cls, tags: ID3) -> Dict[str, Any]:
        """Parse ID3 tags (MP3)."""
        result = {}

        # Text frames
        text_mapping = {
            "TIT2": "title",
            "TPE1": "artist",
            "TALB": "album",
            "TRCK": "track_number",
            "TDRC": "year",
        }

        for frame_id, field in text_mapping.items():
            if frame_id in tags:
                value = str(tags[frame_id].text[0]) if tags[frame_id].text else None
                if value:
                    result[field] = value

        # Extract year from TDRC (which can be full date)
        if "year" in result and len(result["year"]) > 4:
            result["year"] = int(result["year"][:4])

        # Cover art
        if "APIC" in tags:
            result["cover_art"] = tags["APIC"].data

        return result

    @classmethod
    def _parse_vorbis_tags(cls, tags: Any) -> Dict[str, Any]:
        """Parse Vorbis comments (FLAC, OGG)."""
        result = {}

        mapping = {
            "title": "title",
            "artist": "artist",
            "album": "album",
            "tracknumber": "track_number",
            "date": "year",
            "year": "year",
        }

        for tag_key, field in mapping.items():
            if tag_key in tags:
                value = tags[tag_key][0] if tags[tag_key] else None
                if value:
                    result[field] = value

        # Convert track number
        if "track_number" in result:
            try:
                # Handle "1/10" format
                track_str = result["track_number"].split("/")[0]
                result["track_number"] = int(track_str)
            except (ValueError, AttributeError):
                pass

        # Convert year
        if "year" in result:
            try:
                result["year"] = int(str(result["year"])[:4])
            except (ValueError, TypeError):
                pass

        # Cover art (FLAC)
        if hasattr(tags, "pictures") and tags.pictures:
            result["cover_art"] = tags.pictures[0].data

        return result

    @classmethod
    def _parse_mp4_tags(cls, tags: Any) -> Dict[str, Any]:
        """Parse MP4 tags (M4A)."""
        result = {}

        mapping = {
            "\xa9nam": "title",
            "\xa9ART": "artist",
            "\xa9alb": "album",
            "trkn": "track_number",
            "\xa9day": "year",
        }

        for tag_key, field in mapping.items():
            if tag_key in tags:
                value = tags[tag_key]
                if value:
                    if isinstance(value, list) and len(value) > 0:
                        value = value[0]
                    if isinstance(value, tuple) and len(value) > 0:
                        # trkn is (track, total)
                        value = value[0]
                    if value:
                        result[field] = value

        # Convert year
        if "year" in result:
            try:
                result["year"] = int(str(result["year"])[:4])
            except (ValueError, TypeError):
                pass

        # Cover art
        if "covr" in tags and tags["covr"]:
            result["cover_art"] = tags["covr"][0]

        return result

    @classmethod
    def _parse_generic_tags(cls, tags: Any) -> Dict[str, Any]:
        """Generic tag parsing fallback."""
        result = {}

        # Try common attribute names
        for attr in ["title", "artist", "album"]:
            if hasattr(tags, attr):
                value = getattr(tags, attr)
                if value:
                    result[attr] = str(value)

        return result
