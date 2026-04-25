FROM python:3.12-slim AS builder

# Установка системных зависимостей для сборки
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Установка uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Копируем файлы зависимостей
COPY pyproject.toml .

# Создаем виртуальное окружение и устанавливаем зависимости
RUN uv venv /app/.venv && \
    UV_PROJECT_ENVIRONMENT=/app/.venv uv pip install -e .

# --- Runtime Stage ---
FROM python:3.12-slim

# Установка runtime зависимостей (ffmpeg для аудио)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копируем виртуальное окружение и код из билдера
COPY --from=builder /app/.venv /app/.venv
COPY . .

# Активируем окружение через PATH
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]