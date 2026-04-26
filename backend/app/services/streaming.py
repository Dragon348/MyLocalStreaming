"""
Streaming module for music tracks with HTTP Range support and on-the-fly transcoding.

This module implements:
1. HTTP Range requests (206 Partial Content) for seekable streaming
2. FFmpeg on-the-fly transcoding to Opus format
3. LRU cache for transcoded chunks
4. Async subprocess management with concurrency limits
5. Comprehensive error handling
"""

import asyncio
import hashlib
import os
import re
import shutil
from pathlib import Path
from typing import AsyncGenerator, Optional, Dict, Any
from dataclasses import dataclass, field
from collections import OrderedDict
import logging

import aiofiles

from app.config import settings

logger = logging.getLogger(__name__)

# Constants
CHUNK_SIZE = 65536  # 64 KB for streaming
TRANSCODE_CHUNK_SIZE = 32768  # 32 KB for transcoded output
MAX_CONCURRENT_TRANSCODES = 3
DEFAULT_BITRATE = 128  # kbps

# Cache directory
TRANSCODE_CACHE_DIR = Path(settings.cache_dir) / "transcoded"


@dataclass
class CacheEntry:
    """Represents a cached transcoded file with metadata for LRU."""
    path: Path
    size: int
    bitrate: int
    track_id: str
    created_at: float = field(default_factory=lambda: asyncio.get_event_loop().time())
    last_accessed: float = field(default_factory=lambda: asyncio.get_event_loop().time())


class LRUCache:
    """
    LRU cache manager for transcoded files.
    
    Manages cache cleanup based on:
    - Maximum total size (settings.max_cache_size_gb)
    - Least recently used entries
    - Entry age
    """
    
    def __init__(self, max_size_gb: int = 10):
        self.max_size_bytes = max_size_gb * 1024 * 1024 * 1024
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = asyncio.Lock()
        self._current_size = 0
    
    async def _scan_existing_cache(self) -> None:
        """Scan existing cache directory and populate cache tracking."""
        if not TRANSCODE_CACHE_DIR.exists():
            return
        
        for file_path in TRANSCODE_CACHE_DIR.glob("*.opus"):
            try:
                stat = file_path.stat()
                # Parse filename: {track_id}_{bitrate}.opus
                match = re.match(r"([a-f0-9\-]+)_(\d+)\.opus", file_path.name)
                if match:
                    track_id = match.group(1)
                    bitrate = int(match.group(2))
                    key = f"{track_id}_{bitrate}"
                    entry = CacheEntry(
                        path=file_path,
                        size=stat.st_size,
                        bitrate=bitrate,
                        track_id=track_id,
                        created_at=stat.st_ctime,
                        last_accessed=stat.st_atime,
                    )
                    self._cache[key] = entry
                    self._current_size += stat.st_size
            except (OSError, ValueError) as e:
                logger.warning(f"Failed to scan cache file {file_path}: {e}")
    
    async def get(self, track_id: str, bitrate: int) -> Optional[Path]:
        """Get cached file path if exists, updates access time."""
        key = f"{track_id}_{bitrate}"
        async with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if entry.path.exists():
                    # Move to end (most recently used)
                    self._cache.move_to_end(key)
                    entry.last_accessed = asyncio.get_event_loop().time()
                    return entry.path
                else:
                    # File was deleted externally
                    del self._cache[key]
                    self._current_size -= entry.size
            return None
    
    async def add(self, track_id: str, bitrate: int, file_path: Path) -> None:
        """Add new entry to cache after transcoding completes."""
        async with self._lock:
            try:
                stat = file_path.stat()
                key = f"{track_id}_{bitrate}"
                
                # Remove old entry if exists
                if key in self._cache:
                    old_entry = self._cache.pop(key)
                    self._current_size -= old_entry.size
                
                entry = CacheEntry(
                    path=file_path,
                    size=stat.st_size,
                    bitrate=bitrate,
                    track_id=track_id,
                )
                self._cache[key] = entry
                self._current_size += stat.st_size
                
                # Cleanup if over size limit
                await self._cleanup_if_needed()
                
            except OSError as e:
                logger.error(f"Failed to add cache entry {file_path}: {e}")
    
    async def remove(self, track_id: str, bitrate: int) -> None:
        """Remove entry from cache and delete file."""
        key = f"{track_id}_{bitrate}"
        async with self._lock:
            if key in self._cache:
                entry = self._cache.pop(key)
                self._current_size -= entry.size
                try:
                    if entry.path.exists():
                        entry.path.unlink()
                except OSError as e:
                    logger.error(f"Failed to delete cache file {entry.path}: {e}")
    
    async def _cleanup_if_needed(self) -> None:
        """Remove oldest entries until under size limit."""
        while self._current_size > self.max_size_bytes and self._cache:
            # Remove oldest (first) entry
            key, entry = next(iter(self._cache.items()))
            del self._cache[key]
            self._current_size -= entry.size
            try:
                if entry.path.exists():
                    entry.path.unlink()
                    logger.info(f"LRU cleanup: removed {entry.path.name} ({entry.size} bytes)")
            except OSError as e:
                logger.error(f"Failed to delete during cleanup {entry.path}: {e}")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        async with self._lock:
            return {
                "entries": len(self._cache),
                "total_size_bytes": self._current_size,
                "total_size_gb": round(self._current_size / (1024**3), 2),
                "max_size_gb": self.max_size_bytes / (1024**3),
                "utilization_percent": round(
                    (self._current_size / self.max_size_bytes) * 100, 2
                ) if self.max_size_bytes > 0 else 0,
            }


# Global cache instance
_lru_cache: Optional[LRUCache] = None
_concurrent_semaphore: Optional[asyncio.Semaphore] = None
_shutdown_event: Optional[asyncio.Event] = None
_active_transcodes: set = set()


def get_lru_cache() -> LRUCache:
    """Get or create the global LRU cache instance."""
    global _lru_cache
    if _lru_cache is None:
        _lru_cache = LRUCache(max_size_gb=settings.max_cache_size_gb)
        # Initialize cache by scanning existing files
        asyncio.create_task(_lru_cache._scan_existing_cache())
    return _lru_cache


def get_semaphore() -> asyncio.Semaphore:
    """Get or create the concurrency semaphore."""
    global _concurrent_semaphore
    if _concurrent_semaphore is None:
        _concurrent_semaphore = asyncio.Semaphore(MAX_CONCURRENT_TRANSCODES)
    return _concurrent_semaphore


def get_shutdown_event() -> asyncio.Event:
    """Get or create the shutdown event."""
    global _shutdown_event
    if _shutdown_event is None:
        _shutdown_event = asyncio.Event()
    return _shutdown_event


def parse_range_header(range_header: str, file_size: int) -> tuple[int, int]:
    """
    Parse HTTP Range header and return (start, end) byte positions.
    
    Supports formats:
    - bytes=start-end
    - bytes=start- (from start to end of file)
    - bytes=-suffix (last suffix bytes)
    
    Returns:
        tuple: (start_byte, end_byte) inclusive
        
    Raises:
        ValueError: If range is invalid or not satisfiable
    """
    if not range_header:
        return 0, file_size - 1
    
    # Match bytes=start-end or bytes=start- or bytes=-suffix
    match = re.match(r"bytes=(\d*)-(\d*)", range_header)
    if not match:
        raise ValueError(f"Invalid Range header format: {range_header}")
    
    start_str, end_str = match.groups()
    
    if not start_str and not end_str:
        raise ValueError("Range must specify at least start or end")
    
    if start_str and end_str:
        # bytes=start-end
        start = int(start_str)
        end = int(end_str)
    elif start_str:
        # bytes=start-
        start = int(start_str)
        end = file_size - 1
    else:
        # bytes=-suffix (last N bytes)
        suffix = int(end_str)
        start = max(0, file_size - suffix)
        end = file_size - 1
    
    # Validate range
    if start < 0:
        start = 0
    if end >= file_size:
        end = file_size - 1
    if start > end:
        raise ValueError(f"Invalid range: start ({start}) > end ({end})")
    if start >= file_size:
        raise ValueError(f"Range not satisfiable: start ({start}) >= file_size ({file_size})")
    
    return start, end


def get_cache_key(track_id: str, bitrate: int) -> str:
    """Generate cache key for a track/bitrate combination."""
    return f"{track_id}_{bitrate}"


def get_cache_path(track_id: str, bitrate: int) -> Path:
    """Get the cache file path for a track/bitrate combination."""
    TRANSCODE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return TRANSCODE_CACHE_DIR / f"{get_cache_key(track_id, bitrate)}.opus"


async def check_ffmpeg_available() -> bool:
    """Check if FFmpeg is available in the system."""
    try:
        process = await asyncio.create_subprocess_exec(
            "ffmpeg", "-version",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await process.communicate()
        return process.returncode == 0
    except FileNotFoundError:
        return False


class TranscodeError(Exception):
    """Exception raised when transcoding fails."""
    pass


class StreamInterrupted(Exception):
    """Exception raised when client disconnects during streaming."""
    pass


async def transcode_to_cache(
    source_path: Path,
    track_id: str,
    bitrate: int,
) -> Path:
    """
    Transcode audio file to Opus format and save to cache.
    
    Args:
        source_path: Path to source audio file
        track_id: Unique track identifier
        bitrate: Target bitrate in kbps
        
    Returns:
        Path to cached transcoded file
        
    Raises:
        TranscodeError: If FFmpeg fails or file not found
    """
    semaphore = get_semaphore()
    shutdown_event = get_shutdown_event()
    
    async with semaphore:
        # Check shutdown
        if shutdown_event.is_set():
            raise TranscodeError("Server is shutting down")
        
        # Check if already in cache
        lru_cache = get_lru_cache()
        cached_path = await lru_cache.get(track_id, bitrate)
        if cached_path and cached_path.exists():
            logger.debug(f"Cache hit for {track_id} at {bitrate}kbps")
            return cached_path
        
        # Verify source file exists
        if not source_path.exists():
            raise TranscodeError(f"Source file not found: {source_path}")
        
        output_path = get_cache_path(track_id, bitrate)
        
        # Build FFmpeg command
        cmd = [
            "ffmpeg",
            "-i", str(source_path),
            "-c:a", "libopus",
            "-b:a", f"{bitrate}k",
            "-vbr", "on",
            "-frame_duration", "20",
            "-application", "audio",
            "-y",  # Overwrite output
            str(output_path),
        ]
        
        logger.info(f"Starting transcode: {source_path.name} -> {bitrate}kbps Opus")
        
        # Track active transcode
        task_id = f"{track_id}_{bitrate}"
        _active_transcodes.add(task_id)
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            # Wait for completion with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=300  # 5 minute timeout for large files
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.communicate()
                raise TranscodeError(f"Transcoding timeout for {track_id}")
            
            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown FFmpeg error"
                logger.error(f"FFmpeg failed: {error_msg}")
                raise TranscodeError(f"FFmpeg exit code {process.returncode}: {error_msg}")
            
            # Add to cache
            await lru_cache.add(track_id, bitrate, output_path)
            logger.info(f"Transcoding complete: {output_path.name}")
            
            return output_path
            
        finally:
            _active_transcodes.discard(task_id)


async def stream_transcoded_chunked(
    source_path: Path,
    track_id: str,
    bitrate: int,
) -> AsyncGenerator[bytes, None]:
    """
    Stream transcoded audio in chunks, caching the result.
    
    This function:
    1. Checks cache first
    2. If not cached, transcodes on-the-fly while streaming
    3. Saves completed transcode to cache for future requests
    
    Args:
        source_path: Path to source audio file
        track_id: Unique track identifier
        bitrate: Target bitrate in kbps
        
    Yields:
        bytes: Audio chunks
        
    Raises:
        TranscodeError: If transcoding fails
        StreamInterrupted: If client disconnects
    """
    lru_cache = get_lru_cache()
    
    # Check cache first
    cached_path = await lru_cache.get(track_id, bitrate)
    if cached_path and cached_path.exists():
        logger.debug(f"Streaming from cache: {cached_path.name}")
        async with aiofiles.open(cached_path, "rb") as f:
            while chunk := await f.read(CHUNK_SIZE):
                yield chunk
        return
    
    # Transcode to cache first, then stream
    # This approach ensures we don't stream partial files
    output_path = await transcode_to_cache(source_path, track_id, bitrate)
    
    # Stream the cached file
    async with aiofiles.open(output_path, "rb") as f:
        while chunk := await f.read(CHUNK_SIZE):
            yield chunk


async def stream_file_range(
    file_path: Path,
    start: int,
    end: int,
) -> AsyncGenerator[bytes, None]:
    """
    Stream file bytes within a specific range.
    
    Args:
        file_path: Path to file
        start: Start byte position
        end: End byte position (inclusive)
        
    Yields:
        bytes: File chunks
    """
    async with aiofiles.open(file_path, "rb") as f:
        await f.seek(start)
        remaining = end - start + 1
        
        while remaining > 0:
            chunk_size = min(CHUNK_SIZE, remaining)
            chunk = await f.read(chunk_size)
            
            if not chunk:
                break
                
            yield chunk
            remaining -= len(chunk)


async def graceful_shutdown(timeout: float = 10.0) -> None:
    """
    Gracefully shutdown all active transcodes.
    
    Args:
        timeout: Maximum time to wait for transcodes to complete
    """
    logger.info("Initiating graceful shutdown of streaming module")
    
    shutdown_event = get_shutdown_event()
    shutdown_event.set()
    
    if _active_transcodes:
        logger.info(f"Waiting for {len(_active_transcodes)} active transcodes to complete")
        
        start_time = asyncio.get_event_loop().time()
        while _active_transcodes:
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed >= timeout:
                logger.warning(f"Shutdown timeout: forcing termination of {len(_active_transcodes)} transcodes")
                break
            await asyncio.sleep(0.5)
    
    logger.info("Streaming module shutdown complete")


# API Helper Functions

async def handle_stream_request(
    track_id: str,
    file_path: Path,
    range_header: Optional[str],
    transcode: bool = False,
    bitrate: int = DEFAULT_BITRATE,
) -> tuple[int, dict, AsyncGenerator]:
    """
    Handle a streaming request with optional Range and transcoding.
    
    Args:
        track_id: Unique track identifier
        file_path: Path to source audio file
        range_header: HTTP Range header value (or None)
        transcode: Whether to transcode to Opus
        bitrate: Target bitrate for transcoding
        
    Returns:
        tuple: (status_code, headers, content_generator)
        
    Raises:
        HTTPException: For various error conditions
    """
    from fastapi import HTTPException
    
    # Verify file exists
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    file_size = file_path.stat().st_size
    
    if transcode:
        # Transcoded streaming doesn't support Range requests
        # because Opus encoding produces variable-sized output
        if range_header:
            logger.warning(f"Range header ignored for transcoded stream: {range_header}")
        
        try:
            generator = stream_transcoded_chunked(file_path, track_id, bitrate)
            headers = {
                "Content-Type": "audio/ogg",
                "Accept-Ranges": "none",  # Range not supported for transcoded
                "X-Transcoded": "true",
                "X-Bitrate": str(bitrate),
            }
            return 200, headers, generator
            
        except TranscodeError as e:
            logger.error(f"Transcoding failed for {track_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Transcoding failed: {str(e)}")
        except FileNotFoundError as e:
            raise HTTPException(status_code=404, detail="Source file not found")
    
    else:
        # Direct file streaming with Range support
        try:
            start, end = parse_range_header(range_header, file_size)
        except ValueError as e:
            if "not satisfiable" in str(e):
                raise HTTPException(status_code=416, detail="Range not satisfiable")
            raise HTTPException(status_code=400, detail=f"Invalid Range header: {e}")
        
        content_length = end - start + 1
        status_code = 206 if range_header else 200
        
        generator = stream_file_range(file_path, start, end)
        
        headers = {
            "Content-Type": "audio/mpeg",  # Default, will be overridden by actual mime type
            "Content-Length": str(content_length),
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
        }
        
        return status_code, headers, generator


def validate_bitrate(bitrate: int) -> int:
    """
    Validate and normalize bitrate value.
    
    Args:
        bitrate: Requested bitrate in kbps
        
    Returns:
        int: Validated bitrate
        
    Raises:
        HTTPException: If bitrate is invalid
    """
    from fastapi import HTTPException
    
    valid_bitrates = [64, 96, 128, 160, 192, 256, 320]
    
    if bitrate not in valid_bitrates:
        # Find closest valid bitrate
        closest = min(valid_bitrates, key=lambda x: abs(x - bitrate))
        logger.warning(f"Invalid bitrate {bitrate}, using closest valid: {closest}")
        return closest
    
    return bitrate


# cURL examples documentation
CURL_EXAMPLES = """
# cURL Examples for Testing Streaming Endpoint

## 1. Basic Stream (Full File)
curl -X GET "http://localhost:8000/api/v1/stream/{track_id}" \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -o output.mp3

## 2. Range Request (First 1MB)
curl -X GET "http://localhost:8000/api/v1/stream/{track_id}" \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Range: bytes=0-1048575" \\
  -o first_mb.mp3

## 3. Range Request (Bytes 1MB-2MB)
curl -X GET "http://localhost:8000/api/v1/stream/{track_id}" \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Range: bytes=1048576-2097151" \\
  -o second_mb.mp3

## 4. Transcoded Stream (Opus 128kbps)
curl -X GET "http://localhost:8000/api/v1/stream/{track_id}?transcode=true&bitrate=128" \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -o output.opus

## 5. Transcoded Stream (Opus 96kbps for mobile)
curl -X GET "http://localhost:8000/api/v1/stream/{track_id}?transcode=true&bitrate=96" \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -o output_low.opus

## 6. Check Response Headers
curl -I -X GET "http://localhost:8000/api/v1/stream/{track_id}" \\
  -H "Authorization: Bearer YOUR_TOKEN"

## 7. Test Range Support (should return 206)
curl -I -X GET "http://localhost:8000/api/v1/stream/{track_id}" \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Range: bytes=0-0"

## 8. Invalid Range (should return 416)
curl -I -X GET "http://localhost:8000/api/v1/stream/{track_id}" \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Range: bytes=999999999-"

Expected responses:
- 200 OK: Full file stream
- 206 Partial Content: Range request successful
- 404 Not Found: File doesn't exist
- 416 Range Not Satisfiable: Invalid range
- 500 Internal Server Error: Transcoding failure
"""


async def get_cache_stats() -> Dict[str, Any]:
    """Get current cache statistics."""
    lru_cache = get_lru_cache()
    stats = await lru_cache.get_stats()
    stats["active_transcodes"] = len(_active_transcodes)
    stats["max_concurrent"] = MAX_CONCURRENT_TRANSCODES
    return stats
