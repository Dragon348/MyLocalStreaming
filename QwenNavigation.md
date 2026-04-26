# QwenNavigation.md - Структура проекта Music Streaming

## 📁 Обзор проекта

Это проект музыкального стримингового сервиса для семейного использования. Backend написан на **FastAPI** с асинхронной базой данных (PostgreSQL/SQLite) и использованием **SQLModel** для ORM.

---

## 🗂️ Структура директорий

```
/workspace
├── backend/                    # Основной бэкенд код
│   ├── app/                    # Приложение FastAPI
│   │   ├── api/                # API роутеры (endpoints)
│   │   ├── models/             # SQLModel модели (таблицы БД)
│   │   ├── schemas/            # Pydantic схемы (валидация данных)
│   │   ├── services/           # Бизнес-логика
│   │   ├── utils/              # Утилиты (безопасность, зависимости)
│   │   ├── __init__.py
│   │   ├── config.py           # Настройки приложения
│   │   ├── database.py         # Подключение к БД
│   │   └── main.py             # Точка входа FastAPI
│   ├── alembic/                # Миграции базы данных
│   │   ├── versions/           # Файлы миграций
│   │   ├── env.py
│   │   └── script.py.mako
│   ├── pyproject.toml          # Зависимости Python
│   ├── Dockerfile              # Образ Docker для бэкенда
│   ├── alembic.ini             # Конфигурация Alembic
│   └── scanner.py              # Скрипт сканирования библиотеки
├── infra/                      # Инфраструктура
│   └── caddy/                  # Reverse proxy конфигурация
│       └── Caddyfile
├── docker-compose.yml          # Оркестрация контейнеров
├── Readme.md                   # Основная документация
└── MUSIC_STREAMING_SPEC.md     # Спецификация проекта
```

---

## 📄 Описание файлов

### Корневые файлы

| Файл | Назначение |
|------|------------|
| `docker-compose.yml` | Оркестрация сервисов: PostgreSQL, Redis, Backend, Caddy |
| `Readme.md` | Основная документация проекта |
| `MUSIC_STREAMING_SPEC.md` | Подробная спецификация функционала |

### Backend (`/workspace/backend/`)

| Файл | Назначение |
|------|------------|
| `pyproject.toml` | Зависимости проекта (FastAPI, SQLModel, passlib, python-jose, mutagen) |
| `Dockerfile` | Docker образ для бэкенда |
| `alembic.ini` | Конфигурация миграций Alembic |
| `scanner.py` | CLI скрипт для сканирования музыкальной библиотеки |

### Приложение (`/workspace/backend/app/`)

#### Основные файлы

| Файл | Назначение |
|------|------------|
| `main.py` | **Точка входа**. Создание FastAPI приложения, настройка CORS, регистрация роутеров |
| `config.py` | **Настройки**. Загрузка переменных окружения (SECRET_KEY, DATABASE_URL, MUSIC_DIR и т.д.) |
| `database.py` | **Подключение к БД**. Асинхронный движок SQLAlchemy, сессии, инициализация таблиц |

#### API Роутеры (`/workspace/backend/app/api/`)

| Файл | Назначение | Endpoints |
|------|------------|-----------|
| `auth.py` | **Аутентификация**. Регистрация, логин, refresh токена, logout | `POST /api/v1/auth/register`, `POST /api/v1/auth/login`, `POST /api/v1/auth/refresh`, `POST /api/v1/auth/logout` |
| `tracks.py` | **Треки**. Список, поиск, получение по ID, случайные треки, счётчик воспроизведений | `GET /api/v1/tracks`, `GET /api/v1/tracks/{id}`, `GET /api/v1/tracks/random`, `PUT /api/v1/tracks/{id}/play`, `GET /api/v1/tracks/search` |
| `playlists.py` | **Плейлисты**. CRUD плейлистов, добавление/удаление треков, переупорядочивание | `GET/POST /api/v1/playlists`, `GET/PUT/DELETE /api/v1/playlists/{id}`, `POST/DELETE /api/v1/playlists/{id}/tracks`, `PUT /api/v1/playlists/{id}/reorder` |

#### Модели данных (`/workspace/backend/app/models/`)

| Файл | Назначение | Таблицы |
|------|------------|---------|
| `user.py` | **Пользователи**. Данные аккаунта, хеш пароля, статус | `users` |
| `track.py` | **Музыка**. Треки, альбомы, исполнители с метаданными | `tracks`, `albums`, `artists` |
| `playlist.py` | **Плейлисты**. Плейлисты и связь треков с ними | `playlists`, `playlist_tracks` |
| `session.py` | **Сессии**. Refresh токены и сессии устройств | `sessions` |

#### Схемы валидации (`/workspace/backend/app/schemas/`)

| Файл | Назначение | Классы |
|------|------------|--------|
| `auth.py` | **Аутентификация**. Схемы для регистрации, логина, токенов | `UserCreate`, `UserResponse`, `Token`, `LoginRequest`, `RegisterRequest` |
| `track.py` | **Треки**. Схемы для треков, альбомов, исполнителей | `TrackResponse`, `TrackListResponse`, `AlbumResponse`, `ArtistResponse`, `TrackSearchRequest` |
| `playlist.py` | **Плейлисты**. Схемы для создания/обновления плейлистов | `PlaylistCreate`, `PlaylistResponse`, `PlaylistWithTracksResponse`, `PlaylistTrackAdd` |

#### Сервисы (`/workspace/backend/app/services/`)

| Файл | Назначение |
|------|------------|
| `library_scanner.py` | **Сканер библиотеки**. Рекурсивное сканирование директории с музыкой, парсинг метаданных, обновление БД |
| `metadata_parser.py` | **Парсер метаданных**. Извлечение тегов из аудиофайлов (MP3, FLAC, OGG, M4A) через mutagen |

#### Утилиты (`/workspace/backend/app/utils/`)

| Файл | Назначение |
|------|------------|
| `security.py` | **Безопасность**. Хеширование паролей (bcrypt), создание/верификация JWT токенов |
| `deps.py` | **Зависимости**. `get_current_user` - получение текущего пользователя из JWT токена |

### Миграции (`/workspace/backend/alembic/`)

| Файл | Назначение |
|------|------------|
| `env.py` | Конфигурация окружения Alembic |
| `versions/001_initial.py` | Первая миграция - создание всех таблиц |

### Инфраструктура (`/workspace/infra/`)

| Файл | Назначение |
|------|------------|
| `caddy/Caddyfile` | Конфигурация reverse proxy Caddy (маршрутизация запросов к бэкенду) |

---

## 🔑 Ключевые зависимости

- **FastAPI** - веб-фреймворк
- **SQLModel** - ORM (SQLAlchemy + Pydantic)
- **Asyncpg/AIOSQLite** - асинхронные драйверы БД
- **Passlib + bcrypt** - хеширование паролей
- **Python-JOSE** - работа с JWT токенами
- **Mutagen** - парсинг метаданных аудиофайлов
- **Pydantic Settings** - управление настройками

---

## 🚀 Быстрый старт

```bash
# Запуск через Docker Compose
docker-compose up -d

# Сканирование музыкальной библиотеки
docker exec music-backend python scanner.py --music-dir /data/music

# Доступ к API документации
http://localhost/docs
```

---

## 📊 Поток данных

1. **Аутентификация**: `auth.py` → `security.py` (JWT) → `deps.py` (валидация)
2. **Запрос треков**: `tracks.py` → `models/track.py` → БД
3. **Сканирование**: `scanner.py` → `services/library_scanner.py` → `services/metadata_parser.py` → БД

---

## 🔍 Для быстрой навигации

| Если нужно... | Смотри файл |
|---------------|-------------|
| Добавить новый endpoint | `backend/app/api/*.py` |
| Изменить модель данных | `backend/app/models/*.py` |
| Изменить настройки | `backend/app/config.py` |
| Добавить валидацию | `backend/app/schemas/*.py` |
| Изменить логику сканирования | `backend/app/services/library_scanner.py` |
| Изменить безопасность | `backend/app/utils/security.py` |
| Обновить миграции | `backend/alembic/versions/` |
