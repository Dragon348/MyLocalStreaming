FROM python:3.12-slim

WORKDIR /app

# Install FFmpeg and curl for healthcheck
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies (production only)
RUN uv sync --frozen --no-dev

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 music && chown -R music:music /app
USER music

EXPOSE 8000

CMD ["uv", "run", "fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000"]
