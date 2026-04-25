import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Security
    secret_key: str = "changeme-secret-key"
    jwt_secret: str = "changeme-jwt-secret"

    # Database
    database_url: str = "postgresql+asyncpg://music:changeme@postgres:5432/music_streaming"
    redis_url: str = "redis://redis:6379/0"

    # Storage
    music_dir: str = "/data/music"
    cache_dir: str = "/data/cache"
    max_cache_size_gb: int = 10

    # Application
    log_level: str = "INFO"
    environment: str = "production"
    server_host: str = "0.0.0.0"
    server_port: int = 8000

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
