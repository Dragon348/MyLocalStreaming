# Music Streaming Service

Полнофункциональный сервис потокового воспроизведения музыки с веб-интерфейсом, админ-панелью и REST API.

## 🚀 Быстрый старт

### Запуск через Docker (рекомендуется)

```bash
# 1. Создайте файл .env
cp .env.example .env

# 2. Отредактируйте .env и замените секретные ключи
# SECRET_KEY=your-secret-key-change-me-in-production
# JWT_SECRET=your-jwt-secret-change-me-in-production

# 3. Запустите все сервисы
docker-compose up --build -d

# 4. Проверьте статус
docker-compose ps

# 5. Откройте в браузере
# http://localhost:80 - фронтенд и API
# http://localhost:80/docs - API документация (Swagger)
```

### Локальная разработка

Смотрите подробные инструкции в [RUN_INSTRUCTIONS.md](./RUN_INSTRUCTIONS.md)

## 📁 Структура проекта

```
.
├── backend/           # Python/FastAPI бэкенд
│   ├── app/          # Основной код приложения
│   ├── Dockerfile    # Docker образ бэкенда
│   └── pyproject.toml# Зависимости Python
├── web/              # React/Vite фронтенд
│   ├── src/          # Исходный код React
│   ├── Dockerfile    # Docker образ фронтенда
│   └── package.json  # Зависимости Node.js
├── infra/            # Инфраструктурные конфиги
│   └── caddy/        # Caddy reverse proxy
├── docker-compose.yml# Оркестрация контейнеров
├── .env.example      # Шаблон переменных окружения
└── RUN_INSTRUCTIONS.md # Подробная инструкция
```

## 🔧 Сервисы

| Сервис | Порт | Описание |
|--------|------|----------|
| Frontend | 80 | React приложение (через Caddy) |
| Backend API | 80/api/v1 | FastAPI REST API |
| PostgreSQL | 5432 | База данных |
| Redis | 6379 | Кэш и сессии |
| Caddy | 80, 443 | Reverse proxy + HTTPS |

## 🎯 Основные возможности

- **Веб-плеер**: Воспроизведение треков, очередь, shuffle, repeat
- **Админ-панель**: Управление пользователями, треками, сканирование библиотеки
- **API**: Полноценный REST API с JWT аутентификацией
- **Аудио-стриминг**: Потоковая передача аудио с поддержкой перемотки
- **Кэширование**: Redis для сессий и частых запросов

## 📖 Документация

- [Инструкция по запуску](./RUN_INSTRUCTIONS.md) - подробное руководство
- [Спецификация](./MUSIC_STREAMING_SPEC.md) - полная спецификация проекта
- [API Docs](http://localhost:80/docs) - Swagger UI (после запуска)

## 🔐 Безопасность

⚠️ **Важно**: Перед использованием в production обязательно замените:
- `SECRET_KEY` в `.env`
- `JWT_SECRET` в `.env`
- Пароль базы данных `DB_PASSWORD`

## 🛠 Разработка

### Бэкенд (Python/FastAPI)

```bash
cd backend
uv venv
source .venv/bin/activate
uv pip install -e .
uvicorn app.main:app --reload
```

### Фронтенд (React/Vite)

```bash
cd web
npm install
VITE_API_URL=http://localhost:8000/api/v1 npm run dev
```

## 📊 Мониторинг

```bash
# Логи всех сервисов
docker-compose logs -f

# Использование ресурсов
docker stats

# Health check
curl http://localhost:80/health
```

## 🧹 Очистка

```bash
# Остановить сервисы
docker-compose down

# Остановить и удалить тома (данные будут потеряны!)
docker-compose down -v
```

## 📝 Лицензия

MIT