"""Server configuration"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    # Server
    app_name: str = "Newsloom API"
    app_version: str = "1.0.0"
    host: str = "0.0.0.0"
    port: int = 8080
    debug: bool = True

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Database
    db_url: str = "sqlite+aiosqlite:///./data/newsloom.db"

    # Paths
    base_dir: Path = Path(__file__).parent.parent
    data_dir: Path = base_dir / "data"
    reports_dir: Path = base_dir / "reports"
    config_path: Path = base_dir / "config" / "config.yaml"
    sources_config_path: Path = base_dir / "config" / "sources.yaml"

    # JWT (for future auth)
    secret_key: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()
