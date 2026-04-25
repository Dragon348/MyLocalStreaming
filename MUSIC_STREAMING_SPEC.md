# 🎵 Music Streaming Complex — Technical Specification

**Version:** 1.0  
**Target Users:** ≤5 family members  
**Deployment:** Docker / docker-compose  
**Remote Access:** Cloudflare Tunnel (no port forwarding)  
**Date:** 2026-01-15

---

## 1. 🏗 Архитектурная схема

### Границы модулей

Система состоит из трёх основных компонентов:

1. **Backend Server (Python)** — единый монолитный сервис, отвечающий за:
   - HTTP API и стриминг аудио
   - Базу данных метаданных
   - Транскодирование на лету через FFmpeg
   - Авторизацию и сессии
   - Парсинг ID3-тегов

2. **Web Client** — SPA-приложение:
   - Веб-плеер с полным функционалом
   - Админ-панель для управления библиотекой и пользователями

3. **Android Client** — нативное приложение:
   - Интеграция с Media3/ExoPlayer
   - Локальное кэширование треков
   - Офлайн-режим

4. **Infrastructure**:
   - PostgreSQL — хранение метаданных, пользователей, плейлистов
   - Redis — кэш сессий, rate-limiting
   - Cloudflare Tunnel — безопасный удалённый доступ
   - Caddy — reverse proxy с автоматическим HTTPS (локально)

### Mermaid-диаграмма

```mermaid
flowchart TB
    subgraph "External Access"
        CF[Cloudflare Tunnel]
    end

    subgraph "Docker Network"
        CADDY[Caddy Reverse Proxy]
        BACKEND[Python Backend<br/>FastAPI + FFmpeg]
        REDIS[Redis Cache]
        POSTGRES[PostgreSQL DB]
    end

    subgraph "Clients"
        WEB[Web Client<br/>React + Vite]
        ANDROID[Android App<br/>Kotlin + Media3]
    end

    subgraph "Storage"
        MUSIC[(Music Files<br/>/data/music)]
        CACHE[(Transcode Cache<br/>/data/cache)]
    end

    CF --> CADDY
    WEB --> CADDY
    ANDROID --> CADDY

    CADDY --> BACKEND
    BACKEND --> REDIS
    BACKEND --> POSTGRES
    BACKEND --> MUSIC
    BACKEND --> CACHE

    style BACKEND fill:#4CAF50,color:#fff
    style WEB fill:#2196F3,color:#fff
    style ANDROID fill:#FF9800,color:#fff
    style CADDY fill:#9C27B0,color:#fff
    style CF fill:#E91E63,color:#fff
```

---

## 2. 🛠 Стек технологий с обоснованием

### Сервер (Python 3.12+)

| Компонент | Технология | Версия | Обоснование |
|-----------|------------|--------|-------------|
| Фреймворк | FastAPI | 0.115+ | Асинхронность, автогенерация OpenAPI, валидация Pydantic |
| ORM | SQLModel | 0.0.22+ | Типобезопасность, интеграция с Pydantic |
| БД | PostgreSQL | 16+ | Надёжность, полнотекстовый поиск через `tsvector` |
| Кэш | Redis | 7.2+ | Сессии, rate-limiting, временные токены |
| Парсинг тегов | mutagen | 1.47+ | Поддержка ID3v1/v2, FLAC, OGG, MP4 |
| Транскодирование | FFmpeg | 7.0+ | Opus/AAC, on-the-fly стриминг |
| Хэширование | passlib[bcrypt] | 1.7.4 | Безопасное хранение паролей |
| Токены | python-jose[cryptography] | 3.3+ | JWT access/refresh токены |
| Очередь задач | встроенная asyncio | — | Для ≤5 пользователей не нужен Celery |

### Веб-клиент

| Компонент | Технология | Версия | Обоснование |
|-----------|------------|--------|-------------|
| Фреймворк | React | 18.3+ | Экосистема, производительность |
| Сборщик | Vite | 5.4+ | Быстрая сборка, HMR |
| State Management | Zustand | 4.5+ | Минимализм, нет boilerplate как у Redux |
| Роутинг | React Router | 6.26+ | Стандарт де-факто |
| HTTP Client | TanStack Query | 5.56+ | Кэширование, фоновая синхронизация |
| UI | TailwindCSS + shadcn/ui | 3.4+ / 0.9+ | Быстрая разработка, доступность |
| Audio | Howler.js | 2.2+ | Кроссбраузерное аудио, поддержка форматов |

### Android-клиент

| Компонент | Технология | Версия | Обоснование |
|-----------|------------|--------|-------------|
| Язык | Kotlin | 2.0+ | Современный, корутины |
| UI | Jetpack Compose | 1.7+ | Declarative UI, меньше кода |
| Медиа | AndroidX Media3 | 1.4+ | Преемник ExoPlayer, лучшая интеграция |
| DI | Hilt | 2.52+ | Официальный DI от Google |
| Сеть | Ktor Client | 2.3+ | Асинхронность, корутины |
| Кэш | Room + DataStore | 2.6+ / 1.1+ | Локальная БД и настройки |
| Загрузка | WorkManager | 2.9+ | Фоновая загрузка, офлайн-режим |

### Инфраструктура

| Компонент | Технология | Версия | Обоснование |
|-----------|------------|--------|-------------|
| Контейнеризация | Docker + Compose | 27+ / 2.29+ | Стандарт деплоя |
| Reverse Proxy | Caddy | 2.8+ | Автоматический HTTPS, простота |
| Туннель | Cloudflare Tunnel | latest | Без проброса портов, DDoS-защита |
| Мониторинг | встроенные healthchecks | — | Для ≤5 пользователей достаточно |

---

## 3. 📁 Структура репозитория

### Monorepo структура

Единый репозиторий для упрощения разработки и деплоя:

```
music-streaming-complex/
├── docker-compose.yml
├── docker-compose.dev.yml
├── .env.example
├── .gitignore
├── README.md
├── MUSIC_STREAMING_SPEC.md
│
├── backend/
│   ├── pyproject.toml
│   ├── uv.lock
│   ├── Dockerfile
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── track.py
│   │   │   ├── album.py
│   │   │   ├── artist.py
│   │   │   ├── playlist.py
│   │   │   └── session.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── track.py
│   │   │   ├── auth.py
│   │   │   └── playlist.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── tracks.py
│   │   │   ├── playlists.py
│   │   │   ├── search.py
│   │   │   └── admin.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── transcoder.py
│   │   │   ├── metadata_parser.py
│   │   │   ├── search_engine.py
│   │   │   └── auth_service.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── security.py
│   │       └── audio_formats.py
│   └── tests/
│       ├── conftest.py
│       ├── test_auth.py
│       ├── test_tracks.py
│       └── test_transcoding.py
│
├── web/
│   ├── package.json
│   ├── pnpm-lock.yaml
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   ├── Dockerfile
│   ├── index.html
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── router.tsx
│   │   ├── store/
│   │   │   ├── player.ts
│   │   │   ├── auth.ts
│   │   │   └── library.ts
│   │   ├── components/
│   │   │   ├── Player/
│   │   │   ├── Library/
│   │   │   ├── Playlist/
│   │   │   └── Admin/
│   │   ├── hooks/
│   │   ├── pages/
│   │   └── lib/
│   │       ├── api.ts
│   │       └── utils.ts
│   └── public/
│
├── android/
│   ├── build.gradle.kts
│   ├── settings.gradle.kts
│   ├── gradle.properties
│   ├── app/
│   │   ├── build.gradle.kts
│   │   ├── src/
│   │   │   ├── main/
│   │   │   │   ├── AndroidManifest.xml
│   │   │   │   ├── java/com/musicstream/app/
│   │   │   │   │   ├── MainActivity.kt
│   │   │   │   │   ├── MusicApplication.kt
│   │   │   │   │   ├── di/
│   │   │   │   │   ├── data/
│   │   │   │   │   ├── domain/
│   │   │   │   │   ├── ui/
│   │   │   │   │   └── service/
│   │   │   │   └── res/
│   │   │   └── test/
│   │   └── src/androidTest/
│   └── gradle/
│
└── infra/
    ├── caddy/
    │   └── Caddyfile
    └── cloudflare/
        └── tunnel-config.yml
```

### Конфигурации линтеров и CI

**backend/.pre-commit-config.yaml:**
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.9
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.11.2
    hooks:
      - id: mypy
        additional_dependencies: [types-passlib, types-python-jose]
```

**web/package.json (scripts):**
```json
{
  "scripts": {
    "lint": "eslint src --ext .ts,.tsx",
    "format": "prettier --write src",
    "typecheck": "tsc --noEmit",
    "test": "vitest run"
  }
}
```

**CI (.github/workflows/ci.yml):**
```yaml
name: CI
on: [push, pull_request]
jobs:
  backend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install uv && uv sync --directory backend
      - run: uv run pytest backend/tests
  web-build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v3
      - run: cd web && pnpm install && pnpm build
```

---

## 4. 🔌 Серверная часть (Python)

### Фреймворк и зависимости

**backend/pyproject.toml:**
```toml
[project]
name = "music-streaming-backend"
version = "1.0.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi[standard]>=0.115.0",
    "sqlmodel>=0.0.22",
    "asyncpg>=0.30.0",
    "redis[hiredis]>=5.2.0",
    "mutagen>=1.47.0",
    "passlib[bcrypt]>=1.7.4",
    "python-jose[cryptography]>=3.3.0",
    "python-multipart>=0.0.12",
    "aiofiles>=24.1.0",
    "pillow>=10.4.0",
]

[dependency-groups]
dev = [
    "pytest>=8.3.0",
    "pytest-asyncio>=0.24.0",
    "httpx>=0.27.0",
    "ruff>=0.6.0",
    "mypy>=1.11.0",
]
```

### Схема БД (SQLModel модели)

**backend/app/models/user.py:**
```python
from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel
import uuid

class User(SQLModel, table=True):
    __tablename__ = "users"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    username: str = Field(unique=True, index=True, min_length=3, max_length=50)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    is_admin: bool = Field(default=False)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    
    # Лимит кэша на устройстве (в МБ)
    cache_limit_mb: int = Field(default=1024)
```

**backend/app/models/track.py:**
```python
from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel, Relationship
import uuid

class Track(SQLModel, table=True):
    __tablename__ = "tracks"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    title: str = Field(index=True)
    duration_ms: int
    file_path: str = Field(unique=True)
    file_size_bytes: int
    mime_type: str  # audio/mpeg, audio/flac, etc.
    bitrate_kbps: int
    sample_rate_hz: int
    channels: int
    
    # Полнотекстовый поиск
    search_vector: str = Field(sa_column_kwargs={"index": True})
    
    album_id: Optional[str] = Field(default=None, foreign_key="albums.id")
    artist_id: Optional[str] = Field(default=None, foreign_key="artists.id")
    
    play_count: int = Field(default=0)
    last_played: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    album: Optional["Album"] = Relationship(back_populates="tracks")
    artist: Optional["Artist"] = Relationship(back_populates="tracks")

class Album(SQLModel, table=True):
    __tablename__ = "albums"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    title: str = Field(index=True)
    artist_id: Optional[str] = Field(default=None, foreign_key="artists.id")
    release_year: Optional[int] = None
    cover_art_path: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    artist: Optional["Artist"] = Relationship(back_populates="albums")
    tracks: list[Track] = Relationship(back_populates="album")

class Artist(SQLModel, table=True):
    __tablename__ = "artists"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str = Field(unique=True, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    albums: list[Album] = Relationship(back_populates="artist")
    tracks: list[Track] = Relationship(back_populates="artist")
```

**backend/app/models/playlist.py:**
```python
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship
import uuid

class Playlist(SQLModel, table=True):
    __tablename__ = "playlists"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str
    description: Optional[str] = None
    owner_id: str = Field(foreign_key="users.id")
    is_public: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    owner: "User" = Relationship(back_populates="playlists")
    tracks: list["PlaylistTrack"] = Relationship(back_populates="playlist")

class PlaylistTrack(SQLModel, table=True):
    __tablename__ = "playlist_tracks"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    playlist_id: str = Field(foreign_key="playlists.id", index=True)
    track_id: str = Field(foreign_key="tracks.id", index=True)
    position: int
    
    playlist: Playlist = Relationship(back_populates="tracks")
    track: Track = Relationship()
```

**backend/app/models/session.py:**
```python
from datetime import datetime, timedelta
from sqlmodel import Field, SQLModel
import uuid

class Session(SQLModel, table=True):
    __tablename__ = "sessions"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    refresh_token_hash: str = Field(index=True)
    device_name: Optional[str] = None
    ip_address: Optional[str] = None
    expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    @classmethod
    def get_expiry(cls, days: int = 30) -> datetime:
        return datetime.utcnow() + timedelta(days=days)
```

### Стратегия транскодирования

**Формат и битрейт:**
- **Целевой формат:** Opus (`.opus`) в контейнере Ogg
- **Битрейт:** 
  - По умолчанию: 128 kbps (баланс качество/размер)
  - Экономия трафика: 96 kbps (мобильная сеть)
  - Высокое качество: 192 kbps (Wi-Fi, premium)
- **Sample rate:** 48 kHz (нативный для Opus)

**On-the-fly vs превентивное кэширование:**

Для ≤5 пользователей выбираем **гибридный подход**:

1. **On-the-fly транскодирование** при первом запросе
2. **Кэширование результата** в `/data/cache/{track_id}_{bitrate}.opus`
3. **LRU-очистка** кэша при достижении лимита (по умолчанию 10 ГБ)

**backend/app/services/transcoder.py:**
```python
import asyncio
import hashlib
from pathlib import Path
from typing import AsyncGenerator
import aiofiles

TRANSCODE_CACHE_DIR = Path("/data/cache")
MAX_CACHE_SIZE_GB = 10

BITRATE_MAP = {
    "low": 96,
    "medium": 128,
    "high": 192,
}

def get_cache_key(track_id: str, bitrate: int) -> str:
    return f"{track_id}_{bitrate}.opus"

def get_cache_path(track_id: str, bitrate: int) -> Path:
    return TRANSCODE_CACHE_DIR / get_cache_key(track_id, bitrate)

async def transcode_track(
    source_path: Path,
    bitrate_kbps: int,
    output_path: Path
) -> None:
    """Транскодирование через FFmpeg с прогрессом."""
    cmd = [
        "ffmpeg",
        "-i", str(source_path),
        "-c:a", "libopus",
        "-b:a", f"{bitrate_kbps}k",
        "-vbr", "on",
        "-frame_duration", "20",
        "-application", "audio",
        "-y",  # overwrite
        str(output_path),
    ]
    
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    
    _, stderr = await process.communicate()
    
    if process.returncode != 0:
        raise RuntimeError(f"FFmpeg failed: {stderr.decode()}")

async def stream_transcoded(
    source_path: Path,
    bitrate_kbps: int,
    track_id: str
) -> AsyncGenerator[bytes, None]:
    """Стриминг с транскодированием on-the-fly."""
    cache_path = get_cache_path(track_id, bitrate_kbps)
    
    # Если есть в кэше — отдаём
    if cache_path.exists():
        async with aiofiles.open(cache_path, "rb") as f:
            while chunk := await f.read(65536):
                yield chunk
        return
    
    # Транскодирование в реальном времени
    cmd = [
        "ffmpeg",
        "-i", str(source_path),
        "-c:a", "libopus",
        "-b:a", f"{bitrate_kbps}k",
        "-f", "ogg",
        "pipe:1",
    ]
    
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
    )
    
    assert process.stdout
    async for chunk in process.stdout.iter_chunked(65536):
        yield chunk
    
    await process.wait()
    
    # Сохраняем в кэш постфактум (если место есть)
    await _save_to_cache(source_path, bitrate_kbps, track_id)

async def _save_to_cache(source_path: Path, bitrate_kbps: int, track_id: str) -> None:
    """Сохранение в кэш после завершения стриминга."""
    # Проверка места
    await _ensure_cache_space()
    
    cache_path = get_cache_path(track_id, bitrate_kbps)
    await transcode_track(source_path, bitrate_kbps, cache_path)

async def _ensure_cache_space() -> None:
    """LRU-очистка кэша."""
    if not TRANSCODE_CACHE_DIR.exists():
        TRANSCODE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        return
    
    total_size = sum(f.stat().st_size for f in TRANSCODE_CACHE_DIR.glob("*.opus"))
    max_size = MAX_CACHE_SIZE_GB * 1024**3
    
    if total_size < max_size:
        return
    
    # Удаляем старые файлы
    files = sorted(
        TRANSCODE_CACHE_DIR.glob("*.opus"),
        key=lambda f: f.stat().st_mtime
    )
    
    while total_size > max_size and files:
        oldest = files.pop(0)
        total_size -= oldest.stat().st_size
        oldest.unlink()
```

**Обоснование выбора Opus:**
- Лучшее качество при низких битрейтах (96 kbps Opus ≈ 128 kbps AAC)
- Низкая задержка кодирования
- Отличная поддержка на Android (Media3)
- Открытый формат без лицензионных ограничений

**Защита от перегрузки CPU:**
- Максимум 2 одновременных транскодирования на ядро
- Приоритет кэшированным файлам
- Rate-limit на уровне API (макс 3 стрима на пользователя)

### REST API

**Базовый URL:** `https://your-domain.com/api/v1`

#### Auth Endpoints

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/auth/register` | Регистрация нового пользователя |
| POST | `/auth/login` | Логин, получение access/refresh токенов |
| POST | `/auth/refresh` | Обновление access токена |
| POST | `/auth/logout` | Инвалидация сессии |
| GET | `/auth/me` | Текущий пользователь |

**POST /auth/register:**
```json
// Request
{
  "username": "john",
  "email": "john@example.com",
  "password": "securepassword123"
}

// Response 201 Created
{
  "id": "uuid",
  "username": "john",
  "email": "john@example.com",
  "is_admin": false
}

// Response 400 Bad Request
{
  "detail": "Username already exists"
}
```

**POST /auth/login:**
```json
// Request
{
  "username": "john",
  "password": "securepassword123",
  "device_name": "Pixel 8 Pro"
}

// Response 200 OK
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "dGhpcyBpcyBhIHJlZnJlc2g...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

#### Tracks Endpoints

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/tracks` | Список треков (пагинация) |
| GET | `/tracks/{id}` | Детали трека |
| GET | `/tracks/{id}/stream` | Стриминг аудио |
| GET | `/tracks/{id}/stream/transcoded` | Стриминг с транскодированием |
| PUT | `/tracks/{id}/play` | Увеличить счётчик воспроизведений |
| GET | `/tracks/random` | Случайные треки (для shuffle) |

**GET /tracks:**
```
Query params:
  - offset: int (default: 0)
  - limit: int (default: 50, max: 200)
  - artist_id: str (optional)
  - album_id: str (optional)
  - sort: str (default: "title", options: "title", "artist", "created_at")

// Response 200 OK
{
  "items": [...],
  "total": 1234,
  "offset": 0,
  "limit": 50
}
```

**GET /tracks/{id}/stream:**
```
Headers:
  - Range: bytes=0- (optional, для seek)
  - Authorization: Bearer <token>

// Response 200 OK или 206 Partial Content
Content-Type: audio/mpeg (или оригинальный формат)
Content-Length: 12345678
Accept-Ranges: bytes

// Тело: бинарные данные файла
```

**GET /tracks/{id}/stream/transcoded:**
```
Query params:
  - bitrate: str (default: "medium", options: "low", "medium", "high")

Headers:
  - Authorization: Bearer <token>

// Response 200 OK
Content-Type: audio/ogg
Transfer-Encoding: chunked

// Тело: Opus поток
```

#### Playlists Endpoints

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/playlists` | Список плейлистов пользователя |
| POST | `/playlists` | Создать плейлист |
| GET | `/playlists/{id}` | Детали плейлиста |
| PUT | `/playlists/{id}` | Обновить плейлист |
| DELETE | `/playlists/{id}` | Удалить плейлист |
| POST | `/playlists/{id}/tracks` | Добавить треки |
| DELETE | `/playlists/{id}/tracks/{track_id}` | Удалить трек |
| PUT | `/playlists/{id}/reorder` | Изменить порядок треков |

#### Search Endpoint

**GET /search:**
```
Query params:
  - q: str (обязательно)
  - type: str (default: "all", options: "tracks", "albums", "artists", "playlists")
  - limit: int (default: 20, max: 100)

// Response 200 OK
{
  "tracks": [...],
  "albums": [...],
  "artists": [...],
  "playlists": [...]
}
```

#### Admin Endpoints (требуется is_admin)

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/admin/scan` | Сканировать библиотеку |
| GET | `/admin/status` | Статус сервера |
| GET | `/admin/users` | Список пользователей |
| PUT | `/admin/users/{id}` | Редактировать пользователя |
| DELETE | `/admin/users/{id}` | Удалить пользователя |
| POST | `/admin/upload` | Загрузить треки |

**POST /admin/scan:**
```json
// Request
{
  "path": "/data/music",
  "force_rescan": false
}

// Response 202 Accepted
{
  "task_id": "uuid",
  "status": "queued"
}
```

### Обработка стриминга

**Выбранный метод: HTTP Range Requests**

**Обоснование:**
- Нативная поддержка во всех клиентах (веб, Android)
- Позволяет seek без перезагрузки всего файла
- Проще реализации чем HLS для ≤5 пользователей
- Не требует сегментации файлов

**Реализация (backend/app/api/tracks.py):**
```python
from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import StreamingResponse
from pathlib import Path
import aiofiles

router = APIRouter()

CHUNK_SIZE = 65536  # 64 KB

@router.get("/tracks/{track_id}/stream")
async def stream_track(
    track_id: str,
    range_header: str = Header(None, alias="Range"),
    current_user = Depends(get_current_user),
):
    track = await get_track_or_404(track_id)
    file_path = Path(track.file_path)
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    file_size = file_path.stat().st_size
    
    # Обработка Range header
    start = 0
    end = file_size - 1
    
    if range_header:
        range_match = re.match(r"bytes=(\d+)-(\d*)", range_header)
        if range_match:
            start = int(range_match.group(1))
            if range_match.group(2):
                end = int(range_match.group(2))
            else:
                end = file_size - 1
    
    if start >= file_size:
        raise HTTPException(status_code=416, detail="Range not satisfiable")
    
    end = min(end, file_size - 1)
    content_length = end - start + 1
    
    async def iter_file():
        async with aiofiles.open(file_path, "rb") as f:
            await f.seek(start)
            remaining = content_length
            while remaining > 0:
                chunk_size = min(CHUNK_SIZE, remaining)
                chunk = await f.read(chunk_size)
                if not chunk:
                    break
                remaining -= len(chunk)
                yield chunk
    
    headers = {
        "Content-Range": f"bytes {start}-{end}/{file_size}",
        "Accept-Ranges": "bytes",
        "Content-Length": str(content_length),
        "Content-Type": track.mime_type,
    }
    
    status_code = 206 if range_header else 200
    
    return StreamingResponse(
        iter_file(),
        status_code=status_code,
        headers=headers,
        media_type=track.mime_type,
    )
```

---

## 5. 🌐 Веб-клиент

### Архитектура приложения

```
src/
├── main.tsx              # Точка входа
├── App.tsx               # Корневой компонент с роутингом
├── router.tsx            # Маршруты
├── store/                # Zustand stores
│   ├── player.ts         # Состояние плеера
│   ├── auth.ts           # Авторизация
│   └── library.ts        # Библиотека треков
├── components/
│   ├── Player/           # Компоненты плеера
│   │   ├── PlayerBar.tsx
│   │   ├── PlayButton.tsx
│   │   ├── ProgressBar.tsx
│   │   ├── VolumeControl.tsx
│   │   └── QueuePanel.tsx
│   ├── Library/          # Просмотр библиотеки
│   │   ├── TrackList.tsx
│   │   ├── AlbumGrid.tsx
│   │   └── ArtistList.tsx
│   ├── Playlist/         # Управление плейлистами
│   └── Admin/            # Админ-панель
├── hooks/                # Custom hooks
│   ├── useAudio.ts
│   ├── usePlayer.ts
│   └── useAuth.ts
├── pages/                # Страницы
│   ├── Home.tsx
│   ├── Library.tsx
│   ├── Playlist.tsx
│   ├── Search.tsx
│   └── Admin.tsx
└── lib/
    ├── api.ts            # API client
    └── utils.ts          # Утилиты
```

### Управление состоянием плеера

**src/store/player.ts:**
```typescript
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface Track {
  id: string;
  title: string;
  artist: string;
  album: string;
  duration_ms: number;
  file_path: string;
  mime_type: string;
}

interface PlayerState {
  // Текущее состояние
  isPlaying: boolean;
  currentTrack: Track | null;
  currentTime: number;
  duration: number;
  volume: number;
  isMuted: boolean;
  shuffle: boolean;
  repeat: 'off' | 'all' | 'one';
  
  // Очередь
  queue: Track[];
  queueIndex: number;
  
  // Actions
  play: (track: Track, queue?: Track[]) => void;
  pause: () => void;
  toggle: () => void;
  next: () => void;
  previous: () => void;
  seek: (time: number) => void;
  setVolume: (volume: number) => void;
  toggleShuffle: () => void;
  setRepeat: (mode: 'off' | 'all' | 'one') => void;
  addToQueue: (track: Track) => void;
  clearQueue: () => void;
}

export const usePlayerStore = create<PlayerState>()(
  persist(
    (set, get) => ({
      isPlaying: false,
      currentTrack: null,
      currentTime: 0,
      duration: 0,
      volume: 0.8,
      isMuted: false,
      shuffle: false,
      repeat: 'off',
      queue: [],
      queueIndex: -1,
      
      play: (track, queue) => {
        const state = get();
        let newQueue = queue || state.queue;
        let newIndex = newQueue.findIndex(t => t.id === track.id);
        
        if (newIndex === -1) {
          newQueue = [...state.queue, track];
          newIndex = newQueue.length - 1;
        }
        
        set({
          currentTrack: track,
          isPlaying: true,
          queue: newQueue,
          queueIndex: newIndex,
          currentTime: 0,
        });
      },
      
      pause: () => set({ isPlaying: false }),
      
      toggle: () => set((state) => ({ isPlaying: !state.isPlaying })),
      
      next: () => {
        const state = get();
        if (state.queue.length === 0) return;
        
        let nextIndex: number;
        if (state.shuffle) {
          nextIndex = Math.floor(Math.random() * state.queue.length);
        } else {
          nextIndex = (state.queueIndex + 1) % state.queue.length;
        }
        
        const nextTrack = state.queue[nextIndex];
        set({
          currentTrack: nextTrack,
          queueIndex: nextIndex,
          isPlaying: true,
          currentTime: 0,
        });
      },
      
      previous: () => {
        const state = get();
        if (state.currentTime > 5) {
          set({ currentTime: 0 });
          return;
        }
        
        if (state.queue.length === 0) return;
        
        const prevIndex = state.queueIndex > 0 
          ? state.queueIndex - 1 
          : state.queue.length - 1;
        
        const prevTrack = state.queue[prevIndex];
        set({
          currentTrack: prevTrack,
          queueIndex: prevIndex,
          isPlaying: true,
          currentTime: 0,
        });
      },
      
      seek: (time) => set({ currentTime: time }),
      
      setVolume: (volume) => set({ volume, isMuted: volume === 0 }),
      
      toggleShuffle: () => set((state) => ({ shuffle: !state.shuffle })),
      
      setRepeat: (mode) => set({ repeat: mode }),
      
      addToQueue: (track) => 
        set((state) => ({ queue: [...state.queue, track] })),
      
      clearQueue: () => set({ queue: [], queueIndex: -1 }),
    }),
    {
      name: 'player-storage',
      partialize: (state) => ({
        volume,
        shuffle,
        repeat,
      }),
    }
  )
);
```

### Интеграция с API

**src/lib/api.ts:**
```typescript
const BASE_URL = '/api/v1';

class ApiClient {
  private accessToken: string | null = null;
  
  setToken(token: string) {
    this.accessToken = token;
  }
  
  clearToken() {
    this.accessToken = null;
  }
  
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${BASE_URL}${endpoint}`;
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };
    
    if (this.accessToken) {
      headers['Authorization'] = `Bearer ${this.accessToken}`;
    }
    
    const response = await fetch(url, { ...options, headers });
    
    if (!response.ok) {
      if (response.status === 401) {
        // Попытка обновить токен
        await this.refreshToken();
        return this.request<T>(endpoint, options);
      }
      throw new Error(`HTTP ${response.status}`);
    }
    
    return response.json();
  }
  
  async login(username: string, password: string) {
    const data = await this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
    this.setToken(data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    return data;
  }
  
  async refreshToken() {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) throw new Error('No refresh token');
    
    const data = await this.request('/auth/refresh', {
      method: 'POST',
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
    this.setToken(data.access_token);
    return data;
  }
  
  // Tracks
  async getTracks(params: { offset?: number; limit?: number } = {}) {
    const query = new URLSearchParams(params as any);
    return this.request<{ items: Track[]; total: number }>(`/tracks?${query}`);
  }
  
  async getStreamUrl(trackId: string, transcoded = false, bitrate = 'medium') {
    const endpoint = transcoded 
      ? `/tracks/${trackId}/stream/transcoded?bitrate=${bitrate}`
      : `/tracks/${trackId}/stream`;
    return `${BASE_URL}${endpoint}`;
  }
  
  // Playlists
  async getPlaylists() {
    return this.request<Playlist[]>('/playlists');
  }
  
  async createPlaylist(name: string, description?: string) {
    return this.request<Playlist>('/playlists', {
      method: 'POST',
      body: JSON.stringify({ name, description }),
    });
  }
  
  // Search
  async search(query: string, type = 'all') {
    const params = new URLSearchParams({ q: query, type });
    return this.request<SearchResults>(`/search?${params}`);
  }
}

export const api = new ApiClient();
```

### Админ-панель

**Компоненты:**
- **Library Scanner:** Кнопка запуска сканирования, прогресс-бар, лог
- **User Management:** Таблица пользователей, редактирование, удаление
- **Upload:** Drag-and-drop зона для загрузки файлов
- **Server Status:** CPU usage, память, место на диске, активные сессии

**src/pages/Admin.tsx:**
```tsx
export function AdminPage() {
  const [status, setStatus] = useState<ServerStatus | null>(null);
  const [isScanning, setIsScanning] = useState(false);
  
  useEffect(() => {
    const fetchStatus = async () => {
      const data = await api.getAdminStatus();
      setStatus(data);
    };
    fetchStatus();
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, []);
  
  const handleScan = async () => {
    setIsScanning(true);
    await api.startLibraryScan();
    setIsScanning(false);
  };
  
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">Admin Panel</h1>
      
      <section className="mb-8">
        <h2 className="text-xl font-semibold mb-4">Server Status</h2>
        {status && (
          <div className="grid grid-cols-3 gap-4">
            <StatCard label="CPU Usage" value={`${status.cpu_percent}%`} />
            <StatCard label="Memory" value={formatBytes(status.memory_used)} />
            <StatCard label="Disk Free" value={formatBytes(status.disk_free)} />
          </div>
        )}
      </section>
      
      <section className="mb-8">
        <h2 className="text-xl font-semibold mb-4">Library</h2>
        <Button onClick={handleScan} disabled={isScanning}>
          {isScanning ? 'Scanning...' : 'Scan Library'}
        </Button>
      </section>
      
      <section>
        <h2 className="text-xl font-semibold mb-4">Users</h2>
        <UserTable />
      </section>
    </div>
  );
}
```

---

## 6. 📱 Android-клиент

### Интеграция с Media3/ExoPlayer

**app/build.gradle.kts:**
```kotlin
dependencies {
    implementation("androidx.media3:media3-exoplayer:1.4.0")
    implementation("androidx.media3:media3-session:1.4.0")
    implementation("androidx.media3:media3-ui:1.4.0")
    implementation("androidx.media3:media3-datasource-okhttp:1.4.0")
    
    implementation("com.squareup.okhttp3:okhttp:4.12.0")
    implementation("io.ktor:ktor-client-android:2.3.12")
    
    implementation("com.google.dagger:hilt-android:2.52")
    kapt("com.google.dagger:hilt-compiler:2.52")
    
    implementation("androidx.room:room-runtime:2.6.1")
    kapt("androidx.room:room-compiler:2.6.1")
    
    implementation("androidx.datastore:datastore-preferences:1.1.1")
    
    implementation("androidx.work:work-runtime-ktx:2.9.1")
}
```

**DataSource конфигурация (MusicDataSource.kt):**
```kotlin
@HiltAndroidApp
class MusicApplication : Application()

@Module
@InstallIn(SingletonComponent::class)
object DataSourceModule {
    
    @Provides
    @Singleton
    fun provideOkHttpClient(
        @ApplicationContext context: Context
    ): OkHttpClient {
        val cacheSize = 500L * 1024 * 1024 // 500 MB
        
        return OkHttpClient.Builder()
            .cache(Cache(context.cacheDir.resolve("http"), cacheSize))
            .addInterceptor { chain ->
                val request = chain.request().newBuilder()
                    .addHeader("User-Agent", "MusicStream/1.0")
                    .build()
                chain.proceed(request)
            }
            .build()
    }
    
    @Provides
    @Singleton
    fun provideHttpDataSourceFactory(
        okHttpClient: OkHttpClient
    ): HttpDataSource.Factory {
        return OkHttpDataSource.Factory(okHttpClient)
    }
    
    @Provides
    @Singleton
    fun provideExoPlayer(
        @ApplicationContext context: Context,
        httpDataSourceFactory: HttpDataSource.Factory
    ): ExoPlayer {
        val cacheDataSourceFactory = CacheDataSource.Factory()
            .setCache(MusicCache.getCache(context))
            .setUpstreamDataSourceFactory(httpDataSourceFactory)
        
        return ExoPlayer.Builder(context)
            .setMediaSourceFactory(
                ProgressiveMediaSource.Factory(cacheDataSourceFactory)
            )
            .setHandleAudioBecomingNoisy(true)
            .setWakeMode(C.WAKE_MODE_NETWORK)
            .build()
    }
}
```

### Стратегия кэширования

**Лимиты:**
- **По умолчанию:** 1 ГБ (настраивается пользователем до 10 ГБ)
- **Максимум треков:** 1000 (при среднем размере 3 МБ на трек)
- **LRU-эвристика:** удаляются давно не прослушиваемые треки

**MusicCache.kt:**
```kotlin
object MusicCache {
    private const val MAX_CACHE_SIZE_BYTES = 1L * 1024 * 1024 * 1024 // 1 GB
    
    @Volatile
    private var cache: SimpleCache? = null
    
    fun getCache(context: Context): SimpleCache {
        return cache ?: synchronized(this) {
            cache ?: buildCache(context).also { cache = it }
        }
    }
    
    private fun buildCache(context: Context): SimpleCache {
        val cacheDir = context.filesDir.resolve("music_cache")
        
        return SimpleCache(
            cacheDir,
            LeastRecentlyUsedCacheEvictor(MAX_CACHE_SIZE_BYTES)
        )
    }
    
    fun clearCache(context: Context) {
        cache?.release()
        cache = null
        context.filesDir.resolve("music_cache").deleteRecursively()
    }
    
    fun getCacheStats(context: Context): CacheStats {
        val cacheDir = context.filesDir.resolve("music_cache")
        val files = cacheDir.listFiles()?.filter { it.isFile } ?: emptyList()
        
        return CacheStats(
            totalSize = files.sumOf { it.length() },
            trackCount = files.size,
            maxSize = MAX_CACHE_SIZE_BYTES
        )
    }
}

data class CacheStats(
    val totalSize: Long,
    val trackCount: Int,
    val maxSize: Long
)
```

**Офлайн-режим (DownloadWorker.kt):**
```kotlin
@HiltWorker
class DownloadWorker @AssistedInject constructor(
    @Assisted context: Context,
    @Assisted params: WorkerParameters,
    private val trackRepository: TrackRepository,
) : CoroutineWorker(context, params) {
    
    override suspend fun doWork(): Result {
        val playlistId = inputData.getString("playlist_id") ?: return Result.failure()
        
        val playlist = trackRepository.getPlaylistWithTracks(playlistId)
        
        playlist.tracks.forEach { track ->
            try {
                downloadTrack(track)
            } catch (e: Exception) {
                Log.e("DownloadWorker", "Failed to download ${track.id}", e)
            }
        }
        
        return Result.success()
    }
    
    private suspend fun downloadTrack(track: Track) {
        val client = HttpClient(Android())
        val url = "${BuildConfig.API_URL}/tracks/${track.id}/stream/transcoded?bitrate=medium"
        
        val response = client.get(url) {
            headers.append("Authorization", "Bearer ${AuthTokenManager.getAccessToken()}")
        }
        
        val cacheFile = MusicCache.getCache(applicationContext)
            .getCacheFile(track.id)
        
        cacheFile.outputStream().use { output ->
            response.bodyAsChannel().consumeEach { chunk ->
                output.write(chunk.toByteArray())
            }
        }
        
        trackRepository.markAsDownloaded(track.id)
    }
}
```

### Синхронизация с сервером

**PlaylistSyncManager.kt:**
```kotlin
@Singleton
class PlaylistSyncManager @Inject constructor(
    private val apiService: ApiService,
    private val playlistDao: PlaylistDao,
    private val workManager: WorkManager
) {
    suspend fun syncPlaylists(userId: String) {
        val remotePlaylists = apiService.getPlaylists(userId)
        val localPlaylists = playlistDao.getAll()
        
        // Merge logic
        remotePlaylists.forEach { remote ->
            val local = localPlaylists.find { it.serverId == remote.id }
            if (local == null) {
                playlistDao.insert(remote.toLocal())
            } else if (local.updatedAt < remote.updatedAt) {
                playlistDao.update(remote.toLocal())
            }
        }
    }
    
    fun scheduleBackgroundSync() {
        val constraints = Constraints.Builder()
            .setRequiredNetworkType(NetworkType.CONNECTED)
            .setRequiresBatteryNotLow(true)
            .build()
        
        val syncRequest = PeriodicWorkRequestBuilder<SyncWorker>(15, TimeUnit.MINUTES)
            .setConstraints(constraints)
            .build()
        
        workManager.enqueueUniquePeriodicWork(
            "playlist_sync",
            ExistingPeriodicWorkPolicy.KEEP,
            syncRequest
        )
    }
}
```

### Обработка переключения сети

**NetworkMonitor.kt:**
```kotlin
@Singleton
class NetworkMonitor @Inject constructor(
    @ApplicationContext private val context: Context
) {
    private val connectivityManager = 
        context.getSystemService<ConnectivityManager>()!!
    
    private val _networkState = MutableStateFlow(NetworkState.UNKNOWN)
    val networkState: StateFlow<NetworkState> = _networkState.asStateFlow()
    
    init {
        val callback = object : ConnectivityManager.NetworkCallback() {
            override fun onAvailable(network: Network) {
                val capabilities = connectivityManager.getNetworkCapabilities(network)
                _networkState.value = when {
                    capabilities?.hasTransport(NetworkCapabilities.TRANSPORT_WIFI) == true -> 
                        NetworkState.WIFI
                    capabilities?.hasTransport(NetworkCapabilities.TRANSPORT_CELLULAR) == true -> 
                        NetworkState.CELLULAR
                    else -> NetworkState.OFFLINE
                }
            }
            
            override fun onLost(network: Network) {
                _networkState.value = NetworkState.OFFLINE
            }
        }
        
        connectivityManager.registerDefaultNetworkCallback(callback)
    }
    
    fun shouldUseHighBitrate(): Boolean {
        return _networkState.value == NetworkState.WIFI
    }
}

enum class NetworkState {
    WIFI, CELLULAR, OFFLINE, UNKNOWN
}
```

**Использование в плеере:**
```kotlin
@HiltViewModel
class PlayerViewModel @Inject constructor(
    private val player: ExoPlayer,
    private val networkMonitor: NetworkMonitor,
    private val settingsRepository: SettingsRepository
) : ViewModel() {
    
    fun playTrack(track: Track) {
        viewModelScope.launch {
            networkMonitor.networkState.collect { state ->
                val bitrate = when (state) {
                    NetworkState.WIFI -> "high"
                    NetworkState.CELLULAR -> 
                        if (settingsRepository.isDataSaverEnabled) "low" else "medium"
                    NetworkState.OFFLINE -> null
                    NetworkState.UNKNOWN -> "medium"
                }
                
                if (bitrate != null) {
                    val mediaItem = MediaItem.fromUri(
                        "${API_URL}/tracks/${track.id}/stream/transcoded?bitrate=$bitrate"
                    )
                    player.setMediaItem(mediaItem)
                    player.prepare()
                    player.play()
                } else {
                    // Офлайн режим — играть из кэша
                    playFromCache(track)
                }
            }
        }
    }
}
```

---

## 7. 🔐 Безопасность и удалённый доступ

### Авторизация

**Схема:**
- **Access Token:** JWT, срок жизни 1 час
- **Refresh Token:** случайная строка (64 байта), хранится в БД, срок жизни 30 дней
- **Хэширование паролей:** bcrypt с cost=12
- **Сессии:** запись в таблице `sessions` с привязкой к устройству

**backend/app/utils/security.py:**
```python
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
import secrets

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = secrets.token_urlsafe(32)  # В продакшене — из env

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token() -> str:
    return secrets.token_urlsafe(64)

def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
```

**Rate Limiting (Redis):**
```python
from redis import asyncio as aioredis
from functools import wraps
from fastapi import Request, HTTPException

redis = aioredis.from_url("redis://redis:6379/0")

def rate_limit(max_requests: int, window_seconds: int):
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            client_ip = request.client.host
            key = f"rate_limit:{client_ip}:{func.__name__}"
            
            current = await redis.incr(key)
            if current == 1:
                await redis.expire(key, window_seconds)
            
            if current > max_requests:
                raise HTTPException(
                    status_code=429,
                    detail="Too many requests"
                )
            
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator

# Использование
@router.post("/auth/login")
@rate_limit(max_requests=5, window_seconds=60)
async def login(...):
    ...
```

### Удалённый доступ

**Решение: Cloudflare Tunnel**

**Преимущества:**
- Не требуется проброс портов на роутере
- Бесплатный тариф подходит для ≤5 пользователей
- Встроенная защита от DDoS
- Автоматический HTTPS

**Настройка:**

1. **Установка cloudflared (в Docker):**

**docker-compose.yml:**
```yaml
services:
  cloudflared:
    image: cloudflare/cloudflared:latest
    container_name: cloudflared
    restart: unless-stopped
    command: tunnel run
    environment:
      - TUNNEL_TOKEN=${CLOUDFLARE_TUNNEL_TOKEN}
    depends_on:
      - caddy
    networks:
      - music-network
```

2. **Получение токена:**
```bash
# Войти в Cloudflare
cloudflared tunnel login

# Создать туннель
cloudflared tunnel create music-tunnel

# Получить токен (сохранить в .env)
cloudflared tunnel token --cred-file ~/.cloudflared/music-tunnel.json music-tunnel
```

3. **Конфигурация туннеля (infra/cloudflare/tunnel-config.yml):**
```yaml
tunnel: music-tunnel
credentials-file: /etc/cloudflared/creds.json

ingress:
  - hostname: music.yourdomain.com
    service: http://caddy:80
    originRequest:
      noTLSVerify: true
  
  - service: http_status:404
```

4. **Запуск с токеном:**
```bash
docker run -d \
  --name cloudflared \
  -e TUNNEL_TOKEN=your_token_here \
  cloudflare/cloudflared:latest \
  tunnel run
```

**Ограничения бесплатного тарифа:**
- До 50 одновременных подключений (достаточно для семьи)
- Без кастомных правил WAF
- Базовая аналитика

---

## 8. 🐳 Docker-инфраструктура

### docker-compose.yml

```yaml
version: '3.9'

services:
  # ==================== Database ====================
  postgres:
    image: postgres:16-alpine
    container_name: music-postgres
    restart: unless-stopped
    environment:
      POSTGRES_USER: music
      POSTGRES_PASSWORD: ${DB_PASSWORD:-changeme123}
      POSTGRES_DB: music_streaming
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - music-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U music"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7.2-alpine
    container_name: music-redis
    restart: unless-stopped
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    networks:
      - music-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ==================== Backend ====================
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: music-backend
    restart: unless-stopped
    environment:
      DATABASE_URL: postgresql+asyncpg://music:${DB_PASSWORD}@postgres:5432/music_streaming
      REDIS_URL: redis://redis:6379/0
      SECRET_KEY: ${SECRET_KEY}
      MUSIC_DIR: /data/music
      CACHE_DIR: /data/cache
      LOG_LEVEL: INFO
    volumes:
      - music_data:/data/music:ro
      - cache_data:/data/cache
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - music-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # ==================== Web Frontend ====================
  web:
    build:
      context: ./web
      dockerfile: Dockerfile
      args:
        - VITE_API_URL=/api/v1
    container_name: music-web
    restart: unless-stopped
    networks:
      - music-network

  # ==================== Reverse Proxy ====================
  caddy:
    image: caddy:2.8-alpine
    container_name: music-caddy
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./infra/caddy/Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy_data:/data
      - caddy_config:/config
    depends_on:
      - backend
      - web
    networks:
      - music-network

  # ==================== Cloudflare Tunnel ====================
  cloudflared:
    image: cloudflare/cloudflared:latest
    container_name: music-cloudflared
    restart: unless-stopped
    command: tunnel run
    environment:
      - TUNNEL_TOKEN=${CLOUDFLARE_TUNNEL_TOKEN}
    depends_on:
      - caddy
    networks:
      - music-network

# ==================== Networks ====================
networks:
  music-network:
    driver: bridge

# ==================== Volumes ====================
volumes:
  postgres_data:
  redis_data:
  music_data:
  cache_data:
  caddy_data:
  caddy_config:
```

### backend/Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install FFmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 music && chown -R music:music /app
USER music

EXPOSE 8000

CMD ["uv", "run", "fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000"]
```

### web/Dockerfile

```dockerfile
FROM node:20-alpine AS builder

WORKDIR /app

RUN corepack enable && corepack prepare pnpm@latest --activate

COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

COPY . .
ARG VITE_API_URL=/api/v1
ENV VITE_API_URL=$VITE_API_URL

RUN pnpm build

# Production stage
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### infra/caddy/Caddyfile

```caddyfile
{
    auto_https on
    email admin@yourdomain.com
}

:80 {
    redir https://{host}{uri} permanent
}

music.yourdomain.com {
    reverse_proxy /api/v1/* backend:8000
    
    reverse_proxy /static/* backend:8000
    
    reverse_proxy /* web:80
    
    tls internal
}
```

### Команды для сборки и запуска

```bash
# Инициализация .env
cp .env.example .env
# Отредактировать .env, установить пароли и токены

# Сборка и запуск
docker compose up -d --build

# Проверка логов
docker compose logs -f backend

# Остановка
docker compose down

# Пересборка без кэша
docker compose build --no-cache

# Резервное копирование БД
docker compose exec postgres pg_dump -U music music_streaming > backup.sql

# Восстановление БД
docker compose exec -T postgres psql -U music music_streaming < backup.sql
```

---

## 9. 🗺 Поэтапный план разработки

### MVP (Недели 1-2)

**Цель:** Базовая функциональность для тестирования архитектуры

**Задачи:**

**Неделя 1:**
- [ ] Инициализация репозитория, настройка Docker
- [ ] БД модели: User, Track (без отношений)
- [ ] Auth: регистрация, логин, JWT
- [ ] Простой API: список треков, стриминг файлов
- [ ] Базовый веб-плеер (один файл, play/pause)

**Неделя 2:**
- [ ] Парсинг базовых ID3-тегов (название, исполнитель)
- [ ] Сканер библиотеки (рекурсивный обход)
- [ ] Веб-плеер: очередь треков, следующий/предыдущий
- [ ] Деплой на тестовый сервер

**Критерии готовности MVP:**
- Можно зарегистрироваться и войти
- Видно список треков
- Можно включить трек и переключать
- Работает с локальной сетью

---

### v0.5 (Недели 3-4)

**Цель:** Полный функционал для веб-пользователей

**Задачи:**

**Неделя 3:**
- [ ] Транскодирование on-the-fly (Opus, 3 битрейта)
- [ ] Кэширование транскодированных файлов
- [ ] Полная модель БД: Album, Artist, Playlist
- [ ] Парсинг обложек альбомов
- [ ] Полнотекстовый поиск (PostgreSQL tsvector)

**Неделя 4:**
- [ ] Плейлисты: создание, добавление, удаление
- [ ] Shuffle-воспроизведение
- [ ] Админ-панель: сканирование, пользователи
- [ ] Rate limiting, защита от перебора
- [ ] Unit-тесты для критических функций

**Критерии готовности v0.5:**
- Поиск работает быстро (<100ms)
- Транскодирование не блокирует другие запросы
- Можно создать плейлист и слушать в shuffle
- Админ может загрузить музыку и управлять пользователями

---

### v1.0 (Недели 5-6)

**Цель:** Мобильное приложение и удалённый доступ

**Задачи:**

**Неделя 5:**
- [ ] Android: базовое приложение с Media3
- [ ] Интеграция с API, авторизация
- [ ] Кэширование треков на устройстве
- [ ] Офлайн-режим (загрузка плейлистов)
- [ ] Настройка Cloudflare Tunnel

**Неделя 6:**
- [ ] Синхронизация прогресса между устройствами
- [ ] Адаптивный битрейт по типу сети
- [ ] Уведомления в статус-баре Android
- [ ] Оптимизация производительности
- [ ] Документация, финальное тестирование

**Критерии готовности v1.0:**
- Android-приложение доступно для установки
- Можно скачать плейлист и слушать офлайн
- Удалённый доступ работает через домен
- Все 5 членов семьи могут пользоваться одновременно

---

### Тестирование и отладка

**Что проверять:**

1. **Транскодирование под нагрузкой:**
```bash
# Запустить 5 параллельных запросов
for i in {1..5}; do
  curl -H "Authorization: Bearer $TOKEN" \
    "http://localhost:8000/api/v1/tracks/$TRACK_ID/stream/transcoded?bitrate=medium" \
    -o /dev/null &
done
wait

# Мониторинг CPU
docker stats music-backend
```

2. **Поиск производительности:**
```bash
# 1000 запросов поиска
ab -n 1000 -c 10 \
  -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/search?q=rock"
```

3. **Кэширование на Android:**
- Заполнить кэш до лимита
- Проверить LRU-очистку
- Убедиться, что старые треки удаляются

4. **Сетевые переключения:**
- Переключить Wi-Fi ↔ мобильная сеть
- Проверить изменение битрейта
- Убедиться, что воспроизведение не прерывается

---

## 10. 🚀 Команды для быстрого старта

### Инициализация репозитория

```bash
# Клонировать шаблон (или создать с нуля)
git clone https://github.com/yourusername/music-streaming-complex.git
cd music-streaming-complex

# Создать .env
cp .env.example .env

# Сгенерировать секретный ключ
python -c "import secrets; print(secrets.token_urlsafe(32))" >> .env

# Установить зависимости бэкенда
cd backend
uv sync

# Установить зависимости веба
cd ../web
pnpm install
```

### Запуск dev-окружения

```bash
# Запуск всех сервисов
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build

# Только бэкенд (для разработки)
cd backend
uv run fastapi dev app/main.py

# Только веб (с горящей перезагрузкой)
cd web
pnpm dev

# Просмотр логов
docker compose logs -f backend

# Доступ к БД
docker compose exec postgres psql -U music music_streaming

# Очистка кэша
docker compose exec backend rm -rf /data/cache/*
```

### Примеры cURL-запросов

**Регистрация:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123"
  }'
```

**Логин:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123",
    "device_name": "Test Browser"
  }'
```

**Получить список треков:**
```bash
TOKEN="eyJhbGciOiJIUzI1NiIs..."

curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/tracks?limit=10&offset=0"
```

**Стриминг трека (оригинал):**
```bash
TRACK_ID="uuid-here"

curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/tracks/$TRACK_ID/stream" \
  -o track.mp3
```

**Стриминг с транскодированием:**
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/tracks/$TRACK_ID/stream/transcoded?bitrate=low" \
  -o track.opus
```

**Поиск:**
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/search?q=beatles&type=tracks&limit=20"
```

**Создать плейлист:**
```bash
curl -X POST http://localhost:8000/api/v1/playlists \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Favorites",
    "description": "Best songs ever"
  }'
```

**Запустить сканирование библиотеки:**
```bash
curl -X POST http://localhost:8000/api/v1/admin/scan \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "path": "/data/music",
    "force_rescan": false
  }'
```

**Проверить здоровье сервера:**
```bash
curl http://localhost:8000/health
```

---

## Приложение A: Переменные окружения (.env.example)

```bash
# ==================== Security ====================
SECRET_KEY=your-secret-key-here-generate-with-python-secrets
DB_PASSWORD=strong-db-password-here

# ==================== Database ====================
DATABASE_URL=postgresql+asyncpg://music:${DB_PASSWORD}@postgres:5432/music_streaming
REDIS_URL=redis://redis:6379/0

# ==================== Storage ====================
MUSIC_DIR=/data/music
CACHE_DIR=/data/cache
MAX_CACHE_SIZE_GB=10

# ==================== Cloudflare Tunnel ====================
CLOUDFLARE_TUNNEL_TOKEN=your-tunnel-token-from-cloudflare-dashboard

# ==================== Application ====================
LOG_LEVEL=INFO
ENVIRONMENT=production

# ==================== Frontend ====================
VITE_API_URL=https://music.yourdomain.com/api/v1
```

---

## Приложение B: Типичные ошибки и решения

| Ошибка | Причина | Решение |
|--------|---------|---------|
| `FFmpeg not found` | Не установлен в контейнере | Добавить в Dockerfile: `RUN apt-get install -y ffmpeg` |
| `JWT decode error` | Неправильный SECRET_KEY | Убедиться, что одинаковый на всех инстансах |
| `Database connection refused` | PostgreSQL не готов | Добавить healthcheck и depends_on в compose |
| `Cache directory permission denied` | Неправильный пользователь | `chown -R music:music /data/cache` |
| `Cloudflare tunnel not connecting` | Неправильный токен | Пересоздать токен: `cloudflared tunnel token ...` |
| `Android app can't connect` | Неправильный URL | Проверить BuildConfig.API_URL в gradle |
| `Transcoding too slow` | Нет аппаратного ускорения | Использовать более слабый preset или снизить битрейт |

---

**Документ создан:** 2026-01-15  
**Версия спецификации:** 1.0  
**Статус:** Готов к реализации
