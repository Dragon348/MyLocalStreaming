# Инструкция по локальному запуску приложения

## Требования

- Docker и Docker Compose (версия 2.0+)
- Node.js 20+ (для локальной разработки фронтенда)
- Python 3.12+ (для локальной разработки бэкенда)
- uv (менеджер пакетов Python)

## Быстрый старт с Docker

### 1. Клонирование и подготовка

```bash
cd /workspace

# Создайте файл .env с необходимыми переменными окружения
cp .env.example .env  # если существует, или создайте вручную
```

### 2. Создание .env файла

Создайте файл `.env` в корне проекта со следующим содержимым:

```env
# Database
DB_PASSWORD=changeme123

# Security (замените на свои секретные ключи в production!)
SECRET_KEY=your-secret-key-change-me
JWT_SECRET=your-jwt-secret-change-me

# Optional: порты и хосты
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
LOG_LEVEL=INFO
```

### 3. Запуск всех сервисов

```bash
# Сборка и запуск всех контейнеров
docker-compose up --build -d

# Просмотр логов
docker-compose logs -f

# Остановка всех сервисов
docker-compose down

# Остановка с удалением томов (данные будут потеряны!)
docker-compose down -v
```

### 4. Доступ к сервисам

После запуска сервисы будут доступны по следующим адресам:

- **Фронтенд**: http://localhost:80 (через Caddy reverse proxy)
- **Backend API**: http://localhost:80/api/v1
- **API Docs (Swagger)**: http://localhost:80/docs
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

### 5. Проверка здоровья сервисов

```bash
# Проверка статуса всех контейнеров
docker-compose ps

# Health check backend
curl http://localhost:80/health

# Проверка логов конкретного сервиса
docker-compose logs backend
docker-compose logs frontend
docker-compose logs postgres
```

## Локальная разработка (без Docker)

### Backend (Python/FastAPI)

```bash
cd backend

# Установка uv (если не установлен)
pip install uv

# Создание виртуального окружения
uv venv

# Активация виртуального окружения
source .venv/bin/activate  # Linux/Mac
# или
.venv\Scripts\activate  # Windows

# Установка зависимостей
uv pip install -e .

# Запуск сервера разработки
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend будет доступен по адресу: http://localhost:8000
API Docs: http://localhost:8000/docs

### Frontend (React/Vite)

```bash
cd web

# Установка зависимостей
npm install
# или
pnpm install

# Запуск сервера разработки с прокси к backend
VITE_API_URL=http://localhost:8000/api/v1 npm run dev
# или
VITE_API_URL=http://localhost:8000/api/v1 pnpm dev
```

Frontend будет доступен по адресу: http://localhost:5173

### Только Docker для базы данных и Redis

Если вы хотите разрабатывать бэкенд и фронтенд локально, но использовать Docker для БД:

```bash
# Запуск только postgres и redis
docker-compose up -d postgres redis

# Теперь ваши локальные backend и frontend могут подключаться к этим сервисам
```

## Управление музыкой

### Добавление музыки

Музыкальные файлы должны быть размещены в директории, которая монтируется в контейнер:

```bash
# Создание директории для музыки
mkdir -p ./music

# Копирование музыкальных файлов
cp /path/to/your/music/*.mp3 ./music/

# Перезапуск backend для сканирования новой музыки
docker-compose restart backend

# Или запуск сканирования через API
curl -X POST http://localhost:80/api/v1/admin/scan \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

## Админ-панель

1. Откройте http://localhost:80/admin
2. Войдите как администратор (первый пользователь может быть создан через API или при инициализации)
3. Используйте кнопку "Запустить сканирование" для поиска новой музыки
4. Управляйте пользователями и треками через интерфейс

## Troubleshooting

### Проблемы с сборкой frontend

```bash
# Очистка кэша и пересборка
docker-compose build --no-cache frontend
docker-compose up -d frontend
```

### Проблемы с подключением к базе данных

```bash
# Проверка логов postgres
docker-compose logs postgres

# Перезапуск postgres
docker-compose restart postgres

# Проверка подключения из backend
docker-compose exec backend curl http://localhost:8000/health
```

### Сброс всех данных

```bash
# Полная очистка и перезапуск
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

### Порты заняты

Если порты 80, 5432, 6379 или 8000 заняты, измените их в `docker-compose.yml`:

```yaml
ports:
  - "8080:80"  # вместо 80:80
  - "5433:5432"  # вместо 5432:5432
```

## Production развертывание

Для production использования:

1. Замените секретные ключи в `.env` на надежные значения
2. Настройте TLS/SSL сертификаты в Caddyfile
3. Измените `music.yourdomain.com` на ваш домен
4. Настройте backup для volumes (postgres_data, music_data)
5. Рассмотрите использование внешнего S3-хранилища вместо локального volume

## Мониторинг

```bash
# Использование ресурсов контейнерами
docker stats

# Логи всех сервисов в реальном времени
docker-compose logs -f

# Логи конкретного сервиса
docker-compose logs -f backend
```

## Дополнительные команды

```bash
# Вход в контейнер backend
docker-compose exec backend bash

# Вход в контейнер postgres
docker-compose exec postgres psql -U music -d music_streaming

# Вход в контейнер redis
docker-compose exec redis redis-cli

# Перезапуск отдельного сервиса
docker-compose restart backend

# Масштабирование (если поддерживается)
docker-compose up -d --scale backend=2
```
