from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    APP_NAME: str = "Vero"

    DATABASE_URL: str
    SECRET_KEY: str
    JWT_ALGORITMO: str = "HS256"
    # Eventos em tempo real (D12). O padrão aponta para o serviço do docker-compose.
    VALKEY_URL: str = "redis://valkey:6379/0"

    model_config = SettingsConfigDict(
        env_file=[
            BASE_DIR.parent.parent.parent / ".env",
            BASE_DIR.parent.parent / ".env",
            ".env",
        ],
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
